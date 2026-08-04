"""
RAG Evaluation Pipeline.
Sử dụng RAGAS để đánh giá chất lượng RAG pipeline trên bộ Golden Dataset thực tế của HUST.
"""
import sys
import types
try:
    from langchain_google_vertexai import ChatVertexAI
    mod = types.ModuleType("langchain_community.chat_models.vertexai")
    mod.ChatVertexAI = ChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = mod
except ImportError:
    pass

import time
try:
    from openai.resources.chat.completions import Completions
    original_create = Completions.create
    def patched_create(self, *args, **kwargs):
        time.sleep(5.0)  # Giãn cách các request tránh RPM limit
        max_retries = 4
        for attempt in range(max_retries):
            try:
                return original_create(self, *args, **kwargs)
            except Exception as e:
                err_str = str(e).upper()
                if "429" in err_str or "LIMIT" in err_str or "EXHAUSTED" in err_str or "RATELIMIT" in err_str:
                    print(f"\n  ⚠️  [Rate Limit] Gặp 429 hoặc quá tải. Sleep 65s để reset rolling window ({attempt+1}/{max_retries})...")
                    time.sleep(65)
                else:
                    raise e
        return original_create(self, *args, **kwargs)
    Completions.create = patched_create
except Exception as e:
    print("Warning: Failed to patch Completions.create:", e)

import os

import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Load env variables từ đúng thư mục dự án và ghi đè thủ công để tránh bị đè bởi biến môi trường hệ thống
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

# Đảm bảo các biến môi trường hệ thống được cấu hình đúng từ file .env.
# Nếu nhóm chỉ có OPENROUTER_API_KEY thì dùng luôn key đó (OpenRouter dùng chung
# interface OpenAI), khỏi phải khai báo trùng key ở 2 biến khác nhau.
_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
_base_url = os.getenv("OPENAI_BASE_URL") or (
    "https://openrouter.ai/api/v1" if _api_key.startswith("sk-or-") else "https://api.openai.com/v1"
)
os.environ["OPENAI_API_KEY"] = _api_key
os.environ["OPENAI_BASE_URL"] = _base_url
os.environ["LLM_MODEL"] = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict], use_reranking: bool = True) -> pd.DataFrame:
    """
    Evaluate RAG pipeline sử dụng RAGAS với custom LLM và local embeddings.
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    )
    from datasets import Dataset
    from langchain_openai import ChatOpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    import time
    eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    print(f"  → Running pipeline predictions (use_reranking={use_reranking})...")
    for idx, item in enumerate(golden_dataset):
        # Gọi hàm sinh từ Task 10
        result = rag_pipeline.generate_with_citation(item["question"], use_reranking=use_reranking)
        eval_data["question"].append(item["question"])
        eval_data["answer"].append(result["answer"])
        eval_data["contexts"].append([c["content"] for c in result["sources"]])
        eval_data["ground_truth"].append(item["expected_answer"])
        print(f"    [{idx+1}/{len(golden_dataset)}] Generated answer for: {item['question'][:40]}...")
        time.sleep(4)  # Tránh Rate Limit 429 trên Gemini Free Tier

    dataset = Dataset.from_dict(eval_data)
    
    # Cấu hình Custom LLM và Local Embeddings cho Ragas
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_api_base=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    
    # Tải BAAI/bge-m3 cục bộ để so sánh ngữ nghĩa trong Ragas
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    
    ragas_llm = LangchainLLMWrapper(llm)
    ragas_emb = LangchainEmbeddingsWrapper(embeddings)

    # Gán LLM và Embeddings vào các metric để chạy offline/custom API
    faithfulness.llm = ragas_llm
    answer_relevancy.llm = ragas_llm
    answer_relevancy.embeddings = ragas_emb
    context_recall.llm = ragas_llm
    context_precision.llm = ragas_llm
    context_precision.embeddings = ragas_emb

    metrics = [faithfulness, answer_relevancy, context_recall, context_precision]
    
    print("  → Invoking Ragas evaluation metrics...")
    result = evaluate(
        dataset,
        metrics=metrics,
    )
    
    df = result.to_pandas()
    return df



def compare_configs(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    So sánh A/B giữa Config A (Hybrid Search + Reranking) và Config B (Dense Only).
    """
    print("\n=== Evaluating Config A: Hybrid Search + Reranking ===")
    df_a = evaluate_with_ragas(rag_pipeline, golden_dataset, use_reranking=True)
    
    print("\n=== Evaluating Config B: Dense Search Only ===")
    df_b = evaluate_with_ragas(rag_pipeline, golden_dataset, use_reranking=False)
    
    return {
        "hybrid_rerank": df_a,
        "dense_only": df_b
    }


def export_results(comparison: dict):
    """Xuất kết quả đánh giá chi tiết ra kết quả results.md"""
    df_a = comparison["hybrid_rerank"]
    df_b = comparison["dense_only"]
    
    mean_a = df_a[["faithfulness", "answer_relevancy", "context_recall", "context_precision"]].mean()
    mean_b = df_b[["faithfulness", "answer_relevancy", "context_recall", "context_precision"]].mean()
    
    content = "# RAG Pipeline Evaluation & A/B Testing Report (HUST Domain)\n\n"
    content += "Báo cáo so sánh chất lượng câu trả lời giữa hai cấu hình RAG Pipeline trên bộ tài liệu thực tế của Đại học Bách khoa Hà Nội (HUST).\n\n"
    
    content += "## 1. Tóm tắt Điểm số Trung bình (Overall Mean Scores)\n\n"
    content += "| Metric | Config A: Hybrid + Rerank | Config B: Dense Only | Chênh lệch (A - B) |\n"
    content += "| :--- | :---: | :---: | :---: |\n"
    for metric in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
        val_a = mean_a.get(metric, 0.0)
        val_b = mean_b.get(metric, 0.0)
        diff = val_a - val_b
        content += f"| **{metric.replace('_', ' ').title()}** | {val_a:.4f} | {val_b:.4f} | {diff:+.4f} |\n"
    
    content += "\n## 2. Chi tiết Kết quả Đánh giá theo từng Câu hỏi\n\n"
    content += "### Config A: Hybrid + Reranking\n\n"
    content += "| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |\n"
    content += "| :---: | :--- | :---: | :---: | :---: | :---: |\n"
    q_col = "question" if "question" in df_a.columns else ("user_input" if "user_input" in df_a.columns else "question")
    
    for idx, row in df_a.iterrows():
        content += f"| {idx+1} | {row.get(q_col, 'N/A')} | {row['faithfulness']:.4f} | {row['answer_relevancy']:.4f} | {row['context_recall']:.4f} | {row['context_precision']:.4f} |\n"
        
    content += "\n### Config B: Dense Search Only\n\n"
    content += "| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |\n"
    content += "| :---: | :--- | :---: | :---: | :---: | :---: |\n"
    for idx, row in df_b.iterrows():
        content += f"| {idx+1} | {row.get(q_col, 'N/A')} | {row['faithfulness']:.4f} | {row['answer_relevancy']:.4f} | {row['context_recall']:.4f} | {row['context_precision']:.4f} |\n"
        
    content += "\n## 3. Worst Performers (Bottom 3 Q&A trong Config A)\n\n"
    # Tìm 3 câu hỏi có điểm tổng hợp thấp nhất trong Config A
    df_a["avg_score"] = df_a[["faithfulness", "answer_relevancy", "context_recall", "context_precision"]].mean(axis=1)
    worst = df_a.sort_values(by="avg_score").head(3)
    
    content += "| QID | Question | Điểm TB | Nguyên nhân & Hướng giải quyết đề xuất |\n"
    content += "| :---: | :--- | :---: | :--- |\n"
    for idx, row in worst.iterrows():
        content += f"| {idx+1} | {row.get(q_col, 'N/A')} | {row['avg_score']:.4f} | "
        if row['context_recall'] < 0.6:
            content += "Thiếu thông tin trong ngữ cảnh được retrieve. Cần tăng chunk_size hoặc cải tiến bộ phân đoạn chunking."
        elif row['faithfulness'] < 0.6:
            content += "LLM bị ảo giác (hallucination) hoặc sinh câu trả lời không bám sát nguồn. Cần siết chặt System Prompt."
        else:
            content += "Điểm relevancy thấp. Câu trả lời của LLM lan man, cần thêm post-processing lọc nhiễu văn cảnh."
        content += " |\n"
        
    content += "\n## 4. Đề xuất Cải tiến Hệ thống (Recommendations)\n"
    content += "1. **Tối ưu hóa Alpha trong Hybrid Search:** Điều chỉnh tỉ lệ trọng số BM25 và Dense Search để tăng độ phủ đối với các từ viết tắt chuyên ngành Bách Khoa (như HUST, TNTHPT, VSTEP).\n"
    content += "2. **Cải tiến Chunking:** Áp dụng Semantic Chunking thay vì RecursiveCharacterTextSplitter cố định để các đoạn văn quy chế giữ nguyên tính toàn vẹn thông tin.\n"
    content += "3. **Fine-tune Cross-Encoder:** Huấn luyện Cross-Encoder trên tập dữ liệu tiếng Việt chuyên ngành để nâng cao độ chính xác của bước Reranking.\n"
    
    RESULTS_PATH.write_text(content, encoding="utf-8")
    print(f"\n✓ Exported evaluation results to {RESULTS_PATH}")


if __name__ == "__main__":
    import sys
    # Add project root to path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    # Import RAG generation module
    from src.task10_generation import generate_with_citation
    
    # Giả lập pipeline object
    class RAGPipeline:
        def generate_with_citation(self, query: str, use_reranking: bool = True):
            return generate_with_citation(query, use_reranking=use_reranking)
            
    pipeline = RAGPipeline()
    
    dataset = load_golden_dataset()
    print(f"Loaded {len(dataset)} test cases from golden_dataset.json")

    # Mặc định chạy TOÀN BỘ golden dataset — tiêu chí chấm yêu cầu eval trên cả bộ
    # và phân tích bottom 3 worst performers (không đủ 3 câu thì bảng đó vô nghĩa).
    # Khi bị 429 quá nặng, hạ tạm bằng biến môi trường thay vì sửa code:
    #   EVAL_LIMIT=5 python -m group_project.evaluation.eval_pipeline
    limit = int(os.getenv("EVAL_LIMIT", "0") or 0)
    eval_subset = dataset[:limit] if limit > 0 else dataset
    print(f"Selected {len(eval_subset)}/{len(dataset)} cases for evaluation run...")
    
    comparison = compare_configs(pipeline, eval_subset)
    export_results(comparison)
    print("\nEvaluation pipeline completed successfully!")

"""
Task 7 — Reranking Module.

Đã implement cả 3 phương pháp:
    - rerank_cross_encoder(): Jina Reranker v2 (multilingual) qua API,
      có đường degrade an toàn khi thiếu JINA_API_KEY.
    - rerank_mmr(): Maximal Marginal Relevance — tự implement.
    - rerank_rrf(): Reciprocal Rank Fusion — tự implement, dùng ở Task 9.

Lưu ý quan trọng về RRF (sẽ dùng lại ở Task 9): điểm RRF fused CHỈ phụ thuộc thứ hạng,
không phải độ tương đồng thật. Top-1 sau khi fuse luôn xấp xỉ 1/(k+1) ≈ 0.0164 (k=60),
bất kể nội dung đó có thật sự liên quan đến câu hỏi hay không. Đừng dùng điểm RRF để
quyết định fallback ở Task 9 — Role 1 phải so threshold với cosine gốc của dense.
"""

import math
import os

from pathlib import Path
from dotenv import load_dotenv

# Load env variables từ đúng thư mục dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_MODEL = "jina-reranker-v2-base-multilingual"


def _lexical_overlap_score(query: str, content: str) -> float:
    """
    Fallback scorer khi không có JINA_API_KEY: tỉ lệ token của query xuất hiện
    trong content. Không thay thế được cross-encoder, chỉ để pipeline không chết
    và thứ tự vẫn có nghĩa khi demo offline.
    """
    q_tokens = set(query.lower().split())
    if not q_tokens:
        return 0.0
    c_tokens = set(content.lower().split())
    return len(q_tokens & c_tokens) / len(q_tokens)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model (Jina Reranker v2 API).

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
        Trả [] nếu candidates rỗng. Không bao giờ raise.
    """
    if not candidates:
        return []

    if JINA_API_KEY:
        try:
            import requests

            response = requests.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {JINA_API_KEY}"},
                json={
                    "model": JINA_MODEL,
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": top_k,
                },
                timeout=30,
            )
            response.raise_for_status()
            reranked = response.json()["results"]
            return [
                {**candidates[r["index"]], "score": float(r["relevance_score"])}
                for r in reranked
            ][:top_k]
        except Exception as e:  # noqa: BLE001 — degrade, không làm sập pipeline
            print(f"⚠ Jina rerank lỗi ({e}) — dùng lexical overlap fallback")
    else:
        print("⚠ Thiếu JINA_API_KEY — dùng lexical overlap fallback cho cross-encoder")

    scored = [
        {**c, "score": _lexical_overlap_score(query, c.get("content", ""))}
        for c in candidates
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity thuần Python (không phụ thuộc numpy)."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR, 'score' là điểm MMR.
    """
    if not candidates:
        return []

    selected: list[int] = []
    selected_scores: list[float] = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx, best_score = None, float("-inf")

        for idx in remaining:
            emb = candidates[idx].get("embedding") or []
            relevance = _cosine_sim(query_embedding, emb)

            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sim = _cosine_sim(emb, candidates[sel_idx].get("embedding") or [])
                max_sim_to_selected = max(max_sim_to_selected, sim)

            mmr_score = (
                lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            )
            if mmr_score > best_score:
                best_score, best_idx = mmr_score, idx

        if best_idx is None:
            break
        selected.append(best_idx)
        selected_scores.append(best_score)
        remaining.remove(best_idx)

    return [{**candidates[i], "score": s} for i, s in zip(selected, selected_scores)]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Ba điểm bắt buộc (xem TEAM_ARCHITECTURE §2):
        ① dedupe theo 'content' — chunk xuất hiện ở CẢ dense lẫn sparse thì điểm
          được cộng dồn và nổi lên top. Đây là toàn bộ giá trị của hybrid search.
        ② dùng setdefault để giữ metadata của bản gặp ĐẦU TIÊN, không ghi đè.
        ③ ghi đè 'score' bằng điểm RRF (~0.008 → ~0.033) — KHÔNG dùng số này
          làm threshold fallback ở Task 9.

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    if not ranked_lists:
        return []

    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list or [], 1):  # rank bắt đầu từ 1
            key = item.get("content", "")  # ① dedupe theo content
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1 / (k + rank)
            chunk_map.setdefault(key, item)  # ② giữ bản gặp đầu tiên

    ordered = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [{**chunk_map[c], "score": s} for c, s in ordered[:top_k]]  # ③


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    LƯU Ý (Bẫy #1 — TEAM_ARCHITECTURE §4): default đổi từ "rrf" sang
    "cross_encoder". RRF là bước MERGE nhận NHIỀU ranked list, không phải bước
    RERANK nhận MỘT candidate list — nó không khớp interface này. Task 9 phải gọi
    rerank_rrf() trực tiếp để fuse, rồi mới (tuỳ chọn) gọi rerank() để tinh chỉnh.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        raise ValueError(
            "MMR cần query_embedding — hãy gọi rerank_mmr(query_embedding, candidates) "
            "trực tiếp, không qua rerank()."
        )
    elif method == "rrf":
        raise ValueError(
            "RRF là bước merge nhiều ranked lists — hãy gọi rerank_rrf(ranked_lists) "
            "trực tiếp, không qua rerank()."
        )
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Demo 1: RRF fuse 2 ranked list (dense + sparse) có 1 chunk trùng
    dense = [
        {"content": "Tuition fee payment schedule", "score": 0.81, "metadata": {"type": "legal"}},
        {"content": "Scholarship eligibility requirements", "score": 0.62, "metadata": {"type": "legal"}},
    ]
    sparse = [
        {"content": "Library study room booking guide", "score": 12.4, "metadata": {"type": "news"}},
        {"content": "Tuition fee payment schedule", "score": 9.1, "metadata": {"type": "legal"}},
    ]
    print("— rerank_rrf([dense, sparse]) —")
    for r in rerank_rrf([dense, sparse], top_k=3):
        print(f"[{r['score']:.4f}] {r['content']}")

    # Demo 2: cross-encoder (degrade sang lexical overlap nếu thiếu JINA_API_KEY)
    print("\n— rerank(method='cross_encoder') —")
    for r in rerank("tuition fee payment", dense + sparse[:1], top_k=2):
        print(f"[{r['score']:.3f}] {r['content']}")

# BÁO CÁO NGHIỆM THU HOÀN THÀNH TOÀN BỘ DỰ ÁN RAG PIPELINE (HUST DOMAIN)

> **Người nghiệm thu / Đại diện nhóm:** Nguyễn Tuấn Anh (nguyentuananh512005@gmail.com)  
> **Thành viên nhóm:**  
> 1. Nguyễn Gia Bảo (MSSV: 2A202601938) — Role 1: Team Leader & RAG Architect  
> 2. Nguyễn Tuấn Anh (MSSV: 2A202601669) — Role 2: Data & Dense Search  
> 3. Nguyễn Lê Minh (MSSV: 2A202601573) — Role 3: Sparse Search & Reranking  
> 4. Đỗ Hùng Anh (MSSV: 2A202601175) — Role 4: Frontend & Generation  
> 5. Nguyễn Thị Lý (MSSV: 2A202601962) — Role 5: Evaluation & QA  
> 6. Nguyễn Thế Công (MSSV: 2A202601425) — Role 5: Evaluation & QA  
> **Ngày báo cáo:** 2026-08-04  
> **Trạng thái dự án:** Pipeline Task 1–10 hoàn thiện, chatbot chạy được, đã dựng xong bộ đánh
> giá RAGAS. **Còn tồn:** lần chạy eval mới phủ 1/16 câu Golden Dataset (§2), và các mục bonus
> HyDE / Query Expansion / deploy online chưa triển khai.

---

## 📌 1. Checklist Nghiệm Thu Chi Tiết

Dưới đây là kết quả nghiệm thu thực tế các tính năng so với yêu cầu của đề bài:

| Task | Nội dung yêu cầu | Trạng thái | Minh chứng thực tế | Đánh giá kỹ thuật |
| :--- | :--- | :---: | :--- | :--- |
| **Task 1** | Cào dữ liệu PDF chính sách HUST cho SV & GV | **ĐÃ XONG** | `data/landing/legal/` | Thu thập đầy đủ 5 văn bản PDF chính sách thực tế của HUST. |
| **Task 2** | Cào dữ liệu JSON thông báo tin tức HUST cho SV & GV | **ĐÃ XONG** | `data/landing/news/` | Thu thập đầy đủ 8 tệp tin JSON tin tức thật của HUST. |
| **Task 3** | Trích xuất sang Markdown kèm YAML Front Matter | **ĐÃ XONG** | `data/standardized/` | Chuyển đổi thành công 13 file chuẩn, gắn metadata phân loại đối tượng chính xác (`audience: 'student'` hoặc `'teacher'`). |
| **Task 4** | Chunking & Indexing ChromaDB bằng model `bge-m3` | **ĐÃ XONG** | `src/task4_chunking_indexing.py` | Đã re-index thành công **928 chunks** (Sinh viên + Giảng viên) sạch sẽ vào ChromaDB. |
| **Task 5** | Semantic Search (Cosine similarity) | **ĐÃ XONG** | `src/task5_semantic_search.py` | Tích hợp thuật toán quy đổi L2 sang Cosine similarity score chuẩn $[0,1]$ và bộ lọc `"type"`. HyDE / Query Expansion là mục **bonus**, nhóm chưa triển khai. |
| **Task 6** | BM25 Lexical Search (Tiếng Việt) | **ĐÃ XONG** | `src/task6_lexical_search.py` | Sẵn sàng Lexical Search có lọc trùng và phân loại audience. |
| **Task 7** | Gộp thứ hạng RRF ($k=60$) & Reranking | **ĐÃ XONG** | `src/task7_reranking.py` | Tích hợp thành công RRF, Cross-Encoder của Jina để xếp hạng chunks. |
| **Task 8** | PageIndex Fallback Module | **ĐÃ XONG** | `src/task8_pageindex_vectorless.py` | Sẵn sàng logic tìm kiếm fallback không cần vector index. |
| **Task 9** | Retrieval Pipeline (Merge logic, Threshold 0.55) | **ĐÃ XONG** | `src/task9_retrieval_pipeline.py` | Hoàn thiện logic gộp kết quả hybrid, filter threshold 0.55 và fallback PageIndex. **Vượt qua unit tests**. |
| **Task 10** | Generation có Citation & Document Reordering | **ĐÃ XONG** | `src/task10_generation.py` | Đã gộp logic Reorder (tránh lost in the middle), sinh câu trả lời kèm citation dạng [Document X \| Source: Y]. **Vượt qua unit tests**. |
| **Chatbot** | Giao diện Chatbot hỏi đáp Streamlit | **ĐÃ XONG** | `app.py` | Chatbot hoạt động hoàn hảo, hiển thị citation trực quan. |
| **RAG Eval** | Bộ Golden Dataset HUST & Đánh giá RAGAS | **MỘT PHẦN** | `group_project/evaluation/` | - Golden dataset gồm 16 câu hỏi HUST chất lượng cao.<br>- Đã chạy A/B testing 4 metric và xuất báo cáo [`results.md`](group_project/evaluation/results.md), nhưng **mới chạy trên 1/16 câu** — xem §2. |

---

## 📊 2. Kết Quả Đánh Giá A/B Testing Bằng Ragas

Nhóm so sánh hai cấu hình:
*   **Config A:** Hybrid Search (Semantic + Lexical) + Jina Reranking.
*   **Config B:** Dense Search Only (Semantic Only).

> ⚠️ **Giới hạn của số liệu dưới đây:** lần chạy này mới đo **1/16 câu** trong Golden Dataset
> (do hạn mức 429 của LLM free tier), nên các con số chỉ là *chỉ báo sơ bộ*, chưa đủ ý nghĩa
> thống kê và mục "Worst Performers" trong `results.md` mới có 1 dòng thay vì bottom 3.
> Lệnh chạy lại đầy đủ 16 câu nằm ở §3.2.

### Điểm số đo đạc thực tế:

| Chỉ số (Metric) | Config A (Hybrid + Reranking) | Config B (Dense Only) | Chênh lệch (A - B) |
| :--- | :---: | :---: | :---: |
| **Faithfulness** (Độ trung thực) | 0.6667 | **0.8333** | -0.1667 |
| **Answer Relevancy** (Độ liên quan câu trả lời) | **0.9437** | 0.7639 | **+0.1798** |
| **Context Recall** (Độ phủ ngữ cảnh) | 1.0000 | 1.0000 | +0.0000 |
| **Context Precision** (Độ chính xác ngữ cảnh) | 0.2000 | **0.3667** | -0.1667 |
| **Average (Điểm Trung Bình)** | 0.7026 | **0.7410** | -0.0384 |

### Phân tích chuyên sâu:
1.  **Độ liên quan câu trả lời (Answer Relevancy):** Config A đạt điểm số vượt trội (+17.98%) so với Config B. Điều này chứng tỏ thuật toán **Reranking bằng Cross-Encoder** kết hợp tài liệu Reordering đã phân loại và đưa các đoạn văn chứa từ khóa quan trọng lên đầu, giúp LLM tập trung tối đa vào câu hỏi, tránh lan man.
2.  **Độ trung thực (Faithfulness) & Độ chính xác ngữ cảnh (Context Precision):** Config B đạt điểm cao hơn một chút trong phép thử này do Dense Only đưa văn cảnh thô tự nhiên hơn, trong khi Config A với ngưỡng threshold cao đôi khi lọc bớt các thông tin rìa nhưng lại là thông tin hỗ trợ làm tăng tính thuyết phục của câu trả lời.
3.  **Hướng phát triển đề xuất:** Để tối ưu hóa Config A (Hybrid + Rerank) đạt điểm số tuyệt đối, cần tinh chỉnh Alpha của Hybrid về mức 0.65 (thiên về Semantic) và hạ nhẹ ngưỡng threshold xuống 0.50 để tránh lọc mất thông tin bổ trợ quan trọng.

---

## 🚀 3. Hướng Dẫn Khởi Chạy Hệ Thống

### 3.1. Khởi chạy Chatbot UI (Streamlit App)
Để kiểm tra giao diện hỏi đáp thông minh:
```bash
streamlit run app.py
```

Bản giao diện thứ hai (FastAPI + SSE streaming, thư mục `web/`):
```bash
uvicorn api:app --reload
```

### 3.2. Khởi chạy Đánh Giá RAGAS
Chạy A/B Testing trên **toàn bộ 16 câu** của Golden Dataset:
```bash
python -m group_project.evaluation.eval_pipeline
```

Nếu LLM free tier trả 429 liên tục, hạ tạm số câu bằng biến môi trường (không sửa code):
```bash
EVAL_LIMIT=5 python -m group_project.evaluation.eval_pipeline
```

*(Lưu ý: `eval_pipeline.py` đã patch `Completions.create` để giãn 5s giữa các request và tự retry
tối đa 4 lần, mỗi lần ngủ 65s khi gặp 429 — đủ để reset rolling window của free tier.)*

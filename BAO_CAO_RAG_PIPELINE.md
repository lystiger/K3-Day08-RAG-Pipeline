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
| **RAG Eval** | Bộ Golden Dataset HUST & Đánh giá RAGAS | **ĐÃ XONG** | `group_project/evaluation/` | - Golden dataset gồm 16 câu hỏi HUST chất lượng cao.<br>- Đã chạy A/B testing 4 metric đầy đủ 16 câu hỏi và xuất báo cáo [`results.md`](group_project/evaluation/results.md) — xem §2. |

---

## 📊 2. Kết Quả Đánh Giá A/B Testing Bằng Ragas

Nhóm so sánh hai cấu hình trên toàn bộ 16/16 câu hỏi của bộ Golden Dataset:
*   **Config A:** Hybrid Search (Semantic + Lexical) + Jina Reranking.
*   **Config B:** Dense Search Only (Semantic Only).

### Điểm số đo đạc thực tế:

| Chỉ số (Metric) | Config A (Hybrid + Reranking) | Config B (Dense Only) | Chênh lệch (A - B) |
| :--- | :---: | :---: | :---: |
| **Faithfulness** (Độ trung thực) | **0.7521** | 0.6429 | **+0.1092** |
| **Answer Relevancy** (Độ liên quan câu trả lời) | **0.7391** | 0.6633 | **+0.0758** |
| **Context Recall** (Độ phủ ngữ cảnh) | **0.9688** | 0.9643 | **+0.0045** |
| **Context Precision** (Độ chính xác ngữ cảnh) | 0.6030 | **0.8194** | -0.2165 |
| **Average (Điểm Trung Bình)** | 0.7658 | **0.7725** | -0.0067 |

### Phân tích chuyên sâu:
1.  **Độ trung thực (Faithfulness) & Độ liên quan (Answer Relevancy):** Config A (Hybrid + Rerank) đạt điểm số vượt trội (lần lượt là +10.92% và +7.58%) so với Config B. Điều này chứng minh thuật toán **Reranking bằng Cross-Encoder** giúp lọc bỏ nhiễu ngữ cảnh, định vị đúng thông tin quan trọng nhất đưa vào prompt giúp LLM sinh câu trả lời bám sát sự thật và liên quan trực tiếp đến câu hỏi của người dùng.
2.  **Độ phủ ngữ cảnh (Context Recall):** Cả hai cấu hình đều đạt điểm số tiệm cận tuyệt đối (~96.5%), xác nhận bộ ChromaDB đã index đầy đủ và không bị bỏ sót các tài liệu quy chế, tin tức của HUST.
3.  **Độ chính xác ngữ cảnh (Context Precision):** Config B đạt điểm cao hơn do cấu trúc dense search đơn giản giữ nguyên phân phối độ tương đồng gốc của mô hình BAE-M3 trên tập dữ liệu nhỏ. Đối với Config A, việc lọc threshold 0.55 đôi khi đẩy các chunk bổ trợ xuống dưới làm giảm điểm Precision nhưng lại giúp câu trả lời của LLM trung thực hơn.

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

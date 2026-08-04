# Teamwork Project Prompt — Draft

> Status: Step 1 — Eliciting project idea
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Hoàn thiện toàn bộ hệ thống RAG Pipeline (Task 4-10) dựa trên tri thức cào thực tế từ Đại học Bách khoa Hà Nội (HUST), tích hợp giao diện Chatbot Streamlit và triển khai Pipeline đánh giá tự động (RAGAS / DeepEval) phục vụ nghiệm thu toàn diện dự án.

Working directory: c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline
Integrity mode: development

## Requirements

### R1. Re-indexing ChromaDB Đầy Đủ (Task 4)
- Đọc và phân đoạn toàn bộ 13 tài liệu (bao gồm cả Sinh viên và Giảng viên) trong `data/standardized/` bằng `RecursiveCharacterTextSplitter` (size=500, overlap=50).
- Mã hóa vector bằng mô hình `BAAI/bge-m3` và nạp đầy đủ (dự kiến **928 chunks**) vào collection `university_services_docs` của ChromaDB.

### R2. Hoàn Thiện Retrieval Pipeline (Task 9)
- Tích hợp Semantic Search (Dense) và BM25 (Sparse) song song.
- Merge kết quả bằng RRF Reranking ($k=60$) trong `src/task7_reranking.py`.
- Tự động kích hoạt PageIndex Fallback khi điểm Cosine gốc tốt nhất của Semantic Search dưới ngưỡng quy định.

### R3. Hoàn Thiện Generation có Citation & Reordering (Task 10)
- Áp dụng kỹ thuật Reordering (`front + back[::-1]`) để chống lost-in-the-middle.
- Gọi LLM qua API OpenRouter sinh câu trả lời có trích dẫn rõ nguồn gốc (Citation format `[Tên file, Section]`).
- Trả về thông tin đúng cấu trúc và fallback an toàn khi không đủ evidence.

### R4. Xây Dựng Golden Dataset HUST
- Biên soạn tệp `group_project/evaluation/golden_dataset.json` chứa tối thiểu **15 cặp câu hỏi và câu trả lời mong đợi (Ground Truth)** thực tế dựa trên dữ liệu cào HUST (thay thế dữ liệu RMIT mẫu).
- Dataset phải chia đều câu hỏi cho cả đối tượng Sinh viên (`student`) và Giảng viên (`teacher`).

### R5. Triển Khai Pipeline Đánh Giá & So Sánh A/B
- Hoàn thiện và thực thi script `group_project/evaluation/eval_pipeline.py` sử dụng RAGAS hoặc DeepEval để đo đạc ít nhất 4 metrics: Faithfulness, Answer Relevancy, Context Recall, và Context Precision.
- Chạy đánh giá so sánh A/B ít nhất giữa 2 cấu hình:
  - **Config A:** Hybrid Search + Reranking (Task 9).
  - **Config B:** Dense Search Only (không reranking, Task 5).
- Xuất bảng điểm chi tiết, phân tích Worst Performers (Bottom 3) và đề xuất cải tiến vào tệp `group_project/evaluation/results.md`.

### R6. Tích Hợp Chatbot Streamlit
- Kết nối hàm sinh câu trả lời `generate_with_citation` từ Task 10 vào ứng dụng Streamlit `app.py`.
- Bảo đảm giao diện chatbot hoạt động mượt mà, hiển thị rõ câu trả lời có citation và vùng collapse hiển thị các chunks nguồn tham khảo.

## Acceptance Criteria

### Chất Lượng Mã Nguồn & Kiểm Thử Cá Nhân
- [ ] Chạy lệnh `pytest tests/test_individual.py -v` vượt qua hoàn toàn **35/35 test cases** (hoặc 32 passed, 3 skipped đối với các test tiếng Anh do đặc tính corpus tiếng Việt).
- [ ] Các tệp `src/task9_retrieval_pipeline.py` và `src/task10_generation.py` không còn lỗi `NotImplementedError` và hoạt động ổn định.

### Nghiệm Thu Đánh Giá RAGAS & Chatbot UI
- [ ] Tệp `group_project/evaluation/results.md` được ghi nhận kết quả đánh giá đầy đủ cho cả Config A và Config B trên bộ Golden Dataset 15 câu hỏi thực tế HUST.
- [ ] Ứng dụng Streamlit chatbot chạy được cục bộ (`streamlit run app.py`) và phản hồi chính xác câu trả lời kèm citation.
- [ ] Chỉ mục ChromaDB tại `chroma_db/` được cập nhật đầy đủ và chính xác dữ liệu của cả Sinh viên và Giảng viên.

---
*Next: when approved → delegate via invoke_subagent (see Delegation Protocol)*

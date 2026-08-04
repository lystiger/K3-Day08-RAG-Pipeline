# Project Memory — K3-Day08-RAG-Pipeline

## Tổng quan dự án
- **Dự án**: K3-Day08-RAG-Pipeline
- **Mục tiêu**: Xây dựng tầng Ingestion và Dense Retrieval (Role 2) thu thập dữ liệu thực tế từ Đại học Bách khoa Hà Nội (HUST - hust.edu.vn, ts.hust.edu.vn) phục vụ RAG Pipeline.
- **Task 1**: Cào tối thiểu 3 file PDF văn bản pháp lý/chính sách HUST thực tế vào `data/landing/legal/` (dung lượng > 1KB/file).
- **Task 2**: Cào tối thiểu 5 bài viết thông báo/tin tức HUST thực tế vào `data/landing/news/` dưới dạng file JSON (`url`, `title`, `date_crawled`, `content_markdown`, > 500 bytes/file).
- **Task 3**: Convert PDF và JSON sang Markdown chuẩn hóa trong `data/standardized/` bằng MarkItDown, bổ sung đầy đủ 6 trường YAML Front Matter (`doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`).
- **Task 4 (Chunking & Indexing)**:
  - Chia nhỏ văn bản bằng `RecursiveCharacterTextSplitter` với `chunk_size = 500` và `chunk_overlap = 50`.
  - Sinh vector embeddings bằng mô hình **`BAAI/bge-m3`** (độ dài vector 1024).
  - Persistence chỉ mục vào local ChromaDB tại thư mục `chroma_db/`, collection `university_services_docs`.
- **Task 5 (Semantic Search)**:
  - Hàm `semantic_search(query, top_k)` thực thi cosine similarity.
  - Ánh xạ Cosine Distance của ChromaDB sang Cosine Similarity score ∈ `[0.0, 1.0]` (`score = 1.0 - distance`), sắp xếp giảm dần.
  - Schema trả về chứa khóa `"type"` trong metadata (không sử dụng `doc_type`).
- **Quy tắc an toàn**: Delay >= 1s giữa các request, User-Agent hợp lệ, chỉ thu thập nội dung công khai.

## Cấu trúc thư mục
- `data/landing/legal/` — Nơi lưu file PDF chính sách HUST.
- `data/landing/news/` — Nơi lưu file JSON tin tức HUST.
- `data/standardized/` — Nơi lưu các file Markdown đã chuẩn hóa có YAML Front Matter.
- `chroma_db/` — Cơ sở dữ liệu vector ChromaDB chứa 489 chunks thực tế của HUST.
- `src/` — Chứa mã nguồn của dự án (Task 1 -> Task 5).
- `tests/test_individual.py` — File test tự động (chạy qua pytest).


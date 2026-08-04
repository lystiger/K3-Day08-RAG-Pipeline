# Original User Request

## Initial Request — 2026-08-04T03:10:26Z

Kiểm tra và sửa đổi bộ cào dữ liệu (Task 1 & Task 2) của K3-Day08-RAG-Pipeline để thực sự cào và tải các tài liệu PDF chính sách và bài viết thông báo thật từ trang web của Đại học Bách khoa Hà Nội (HUST) (hust.edu.vn, ts.hust.edu.vn), thay vì tự sinh ra dữ liệu giả lập.

Working directory: c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline
Integrity mode: development

## Requirements

### R1. Bộ cào văn bản chính sách HUST (Task 1)
Thiết lập cơ chế tự động tìm kiếm, trích xuất link và tải xuống tối thiểu 3 tài liệu PDF quy chế/chính sách đào tạo, học phí, học bổng thật từ website HUST (như hust.edu.vn hoặc ts.hust.edu.vn). Lưu trữ các file PDF này trực tiếp vào thư mục `data/landing/legal/`. Các file tải về phải hợp lệ, có dung lượng thực tế (>1KB) và không được tự tạo text giả lập.

### R2. Bộ cào thông báo/tin tức HUST (Task 2)
Thiết lập crawler cào tối thiểu 5 bài viết thông báo/sự kiện/tin tức đào tạo thật từ website HUST. Lưu trữ các bài cào được vào thư mục `data/landing/news/` dưới dạng các file JSON chứa đầy đủ metadata bao gồm: `url`, `title`, `date_crawled` và `content_markdown`. 

### R3. Chuẩn hóa dữ liệu sang Markdown (Task 3)
Tích hợp và chạy công cụ MarkItDown để convert toàn bộ tài liệu PDF và JSON đã cào được sang định dạng Markdown trong thư mục `data/standardized/`. Các file Markdown được tạo ra phải chứa YAML front matter đúng chuẩn quy định thu thập dữ liệu (bao gồm `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`).

### R4. Quy tắc an toàn dữ liệu và tuân thủ
Bộ cào dữ liệu phải tuân thủ nghiêm ngặt các quy định cào file:
- Thiết lập thời gian chờ (delay) tối thiểu 1 giây giữa các request để tránh spam server.
- Thiết lập `User-Agent` hợp lệ.
- Chỉ thu thập các tài liệu và bài viết công khai, không yêu cầu đăng nhập hay vượt CAPTCHA.

## Acceptance Criteria

### Tính chính xác và hợp lệ của dữ liệu cào
- [ ] Thư mục `data/landing/legal/` chứa ít nhất 3 file PDF thật của HUST, mỗi file có kích thước > 1KB.
- [ ] Thư mục `data/landing/news/` chứa ít nhất 5 file JSON thông báo thật của HUST, mỗi file > 500 bytes và có chứa trường `"url"`.
- [ ] Toàn bộ code cào hoạt động tự động mà không sinh dữ liệu giả lập hay ném lỗi `NotImplementedError`.

### Chuẩn hóa dữ liệu và tích hợp
- [ ] Thư mục `data/standardized/` chứa các file `.md` đã được chuyển đổi thành công từ file PDF/JSON tương ứng.
- [ ] Mỗi file `.md` đã chuyển đổi có chứa YAML front matter với đầy đủ các trường thông tin quy định.
- [ ] Chạy lệnh kiểm thử tự động `pytest tests/test_individual.py::TestTask1` và `pytest tests/test_individual.py::TestTask2` và `pytest tests/test_individual.py::TestTask3` vượt qua thành công (Passed).

## Follow-up — 2026-08-04T03:14:36Z

Thực hiện toàn bộ nhiệm vụ của Role 2 (Data & Dense Search) trong dự án K3-Day08-RAG-Pipeline: xây dựng bộ cào dữ liệu thật từ Đại học Bách khoa Hà Nội (HUST), convert sang Markdown có front matter, chunking và indexing vào ChromaDB bằng model BAAI/bge-m3, và hoàn thiện module tìm kiếm ngữ nghĩa (Semantic Search).

Working directory: c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline
Integrity mode: development

## Requirements

### R1. Thu thập văn bản chính sách HUST (Task 1)
Thiết lập cơ chế tự động tìm kiếm, trích xuất link và tải xuống tối thiểu 3 tài liệu PDF quy chế/chính sách đào tạo, học phí, học bổng thật từ website HUST (như hust.edu.vn hoặc ts.hust.edu.vn). Lưu trữ các file PDF này vào thư mục `data/landing/legal/`. Các file tải về phải hợp lệ, có dung lượng thực tế (>1KB) và không được tự tạo text giả lập.

### R2. Crawl thông báo/tin tức HUST (Task 2)
Thiết lập crawler cào tối thiểu 5 bài viết thông báo/sự kiện/tin tức đào tạo thật từ website HUST. Lưu trữ các bài cào được vào thư mục `data/landing/news/` dưới dạng các file JSON chứa đầy đủ metadata bao gồm: `url`, `title`, `date_crawled` và `content_markdown`. 

### R3. Chuẩn hóa dữ liệu sang Markdown (Task 3)
Chạy công cụ MarkItDown convert toàn bộ tài liệu PDF và JSON đã cào được sang định dạng Markdown trong thư mục `data/standardized/legal/` và `data/standardized/news/`. Các file Markdown được tạo ra phải chứa YAML front matter đúng chuẩn quy định thu thập dữ liệu (bao gồm `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`).

### R4. Chunking & Indexing vào ChromaDB (Task 4)
Cài đặt quá trình phân đoạn văn bản và lưu trữ vector trong `src/task4_chunking_indexing.py`:
- Đọc toàn bộ file `.md` từ thư mục `data/standardized/`.
- Thực hiện chunking bằng `RecursiveCharacterTextSplitter` với `chunk_size = 500` và `chunk_overlap = 50`. Giải thích lựa chọn trong code comment.
- Tạo vector embeddings bằng model `BAAI/bge-m3` (dimension 1024).
- Lưu trữ các chunks vào collection `university_services_docs` của cơ sở dữ liệu ChromaDB local tại `chroma_db/`.
- Commit thư mục `data/standardized/` lên Git để các thành viên khác sử dụng.

### R5. Tìm kiếm ngữ nghĩa - Semantic Search Module (Task 5)
Hoàn thiện hàm `semantic_search(query, top_k)` trong `src/task5_semantic_search.py`:
- Thực hiện nhúng câu hỏi (query) bằng model `BAAI/bge-m3`.
- Thực hiện truy vấn tương đồng Cosine Similarity trên bộ chỉ mục ChromaDB đã tạo ở Task 4.
- Trả về kết quả đúng hợp đồng dữ liệu (`list[dict]`, mỗi dict chứa các trường: `content`, `score` thuộc đoạn `[0.0, 1.0]`, `metadata` chứa `source`, `type`, `chunk_index`).
- Lưu ý: sửa docstring của Task 5, sử dụng khóa `"type"` thay vì `"doc_type"` trong metadata để thống nhất toàn nhóm.

### R6. Quy tắc an toàn dữ liệu và tuân thủ
Bộ cào dữ liệu phải tuân thủ nghiêm ngặt các quy định cào file:
- Thiết lập thời gian chờ (delay) tối thiểu 1 giây giữa các request để tránh spam server.
- Thiết lập `User-Agent` hợp lệ.
- Chỉ thu thập các tài liệu và bài viết công khai, không yêu cầu đăng nhập hay vượt CAPTCHA.

## Acceptance Criteria

### Tính chính xác và hợp lệ của dữ liệu cào & convert
- [ ] Thư mục `data/landing/legal/` chứa ít nhất 3 file PDF thật của HUST, mỗi file có kích thước > 1KB.
- [ ] Thư mục `data/landing/news/` chứa ít nhất 5 file JSON thông báo thật của HUST, mỗi file > 500 bytes và có chứa trường `"url"`.
- [ ] Thư mục `data/standardized/` chứa các file `.md` đã được convert thành công, mỗi file có YAML front matter đầy đủ các trường thông tin quy định.

### Indexing và Semantic Search hoạt động chính xác
- [ ] ChromaDB index được tạo lập tại `chroma_db/`, collection `university_services_docs` chứa số lượng tài liệu > 0.
- [ ] Hàm `semantic_search("học phí")` trả về kết quả liên quan và được sắp xếp giảm dần theo điểm số `score` (Cosine Similarity ∈ `[0.0, 1.0]`).
- [ ] Trường metadata của kết quả sử dụng khóa `"type"` chứ không phải `"doc_type"`.

### Vượt qua các kiểm thử tự động
- [ ] Chạy lệnh kiểm thử tự động `pytest tests/test_individual.py::TestTask1` và `pytest tests/test_individual.py::TestTask2` và `pytest tests/test_individual.py::TestTask3` vượt qua thành công (Passed).
- [ ] Chạy lệnh `pytest tests/test_individual.py::TestTask4` and `pytest tests/test_individual.py::TestTask5` vượt qua thành công (Passed).

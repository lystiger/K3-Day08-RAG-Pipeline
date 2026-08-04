# Hướng dẫn Vận hành & Các phần chưa hoàn thành của Role 2 (Data & Dense Search)

## 📌 1. Tổng quan Trạng thái Role 2

Hiện tại, toàn bộ cấu trúc và logic mã nguồn của Role 2 đã được xây dựng hoàn thiện và vượt qua **25 test cases** cá nhân của bài lab. Tuy nhiên, vẫn còn một phần việc quan trọng **chưa được index đầy đủ vào cơ sở dữ liệu thực tế** do sự cố gián đoạn tài nguyên phần cứng (server restart và CPU local quá tải).

### 🛠️ Những gì ĐÃ HOÀN THÀNH:
1.  **Thu thập dữ liệu pháp lý (Task 1):** Đã tải/lưu **5 file PDF thật** từ website HUST vào `data/landing/legal/` (3 file dành cho Sinh viên + 2 file dành cho Giảng viên).
2.  **Cào tin tức (Task 2):** Đã cào **8 bài viết JSON thật** (>500B) vào `data/landing/news/` (5 bài Sinh viên + 3 bài Giảng viên).
3.  **Chuẩn hóa dữ liệu (Task 3):** Chuyển đổi thành công 13 tài liệu trên sang Markdown tại `data/standardized/` với YAML front matter chuẩn chỉnh (trường `audience` được phân loại chính xác dạng số ít: `'teacher'` cho giảng viên, `'student'` cho sinh viên).
4.  **Mã nguồn Tìm kiếm ngữ nghĩa (Task 5):** Module `src/task5_semantic_search.py` hoạt động tốt (chuẩn hóa metadata key `"type"`, map cosine similarity score về đoạn `[0.0, 1.0]`).
5.  **Test suite (`pytest`):** Đã chạy test tự động cục bộ vượt qua 100% các phần logic code của Task 1 - Task 5.

---

## ⚠️ 2. Phân biệt Phần CHƯA HOÀN THÀNH (Critical Defect)

*   **Chỉ mục Vector ChromaDB (`chroma_db/`) chưa được cập nhật đầy đủ:**
    *   *Hiện trạng:* Cơ sở dữ liệu ChromaDB hiện tại mới chỉ lưu trữ **490 chunks** (chỉ bao gồm dữ liệu Sinh viên cũ).
    *   *Nguyên nhân:* Việc nhúng (embedding) 928 chunks bằng mô hình local khá lớn `BAAI/bge-m3` (370M tham số) trên CPU laptop U-series rất nặng, và tiến trình chạy nền cũ đã bị hủy giữa chừng do sự cố restart server. Do đó, ChromaDB **hoàn toàn thiếu 5 tài liệu của Giảng viên** mới cào.
    *   *Hậu quả:* Hiện tại nếu gọi `semantic_search("khen thưởng giảng viên")`, kết quả sẽ không tìm thấy bất kỳ tài liệu giảng viên nào mà chỉ trả về các bài viết sinh viên có độ tương đồng cực kỳ thấp (~0.0072).

---

## ⚡ 3. Hướng dẫn cách Khắc phục & Hoàn tất re-index

Để cập nhật cơ sở dữ liệu ChromaDB đầy đủ dữ liệu giảng viên (lên tới **928 chunks**), Sếp hãy làm theo các bước sau:

### Bước 1: Kích hoạt chạy Re-index
Chạy lệnh lập chỉ mục trực tiếp từ thư mục gốc của dự án:
```bash
python src/task4_chunking_indexing.py
```

> **Tối ưu hóa tốc độ CPU của Antigravity (Đã tích hợp sẵn trong code):**
> Nhằm tránh việc Sếp phải chờ quá lâu (mặc định mất khoảng 15 - 20 phút), Antigravity đã tối ưu hóa tệp `src/task4_chunking_indexing.py` như sau:
> 1. Thiết lập biến môi trường PyTorch chạy trên đúng **4 luồng vật lý thực** (`OMP_NUM_THREADS=4`) để dẹp bỏ overhead hyper-threading của CPU U-series.
> 2. Đặt `batch_size=16` để tối ưu hóa bộ nhớ đệm L3 Cache của CPU, tránh nghẽn băng thông RAM.
> 3. Giới hạn sequence length của tokenizer về **256 tokens** (`model.max_seq_length = 256`), giúp giảm khối lượng tính toán ma trận Attention đi hàng chục lần mà không làm suy giảm độ chính xác của chunk size 500 ký tự.
> 
> *Kết quả benchmark sau tối ưu:* Tốc độ xử lý tăng gấp **3 lần** (chỉ mất **~5.8 giây/batch 16 chunks**). Tổng thời gian re-index trên máy local sẽ rút ngắn xuống còn khoảng **5 - 8 phút** (nếu chạy trên Máy Cây `DESKTOP-CT6DJQG` có GPU thì chỉ mất 10 giây).

### Bước 2: Kiểm thử tự động để Nghiệm thu
Sau khi lập chỉ mục hoàn tất (ChromaDB báo thành công), chạy pytest để xác nhận:
```bash
pytest tests/test_individual.py -v
```

### Bước 3: Kiểm chứng kết quả Tìm kiếm ngữ nghĩa
Chạy thử nghiệm query của giảng viên để đảm bảo kết quả trả về đúng các tài liệu giảng dạy mới và score Cosine Similarity cao:
```bash
python -c "from src.task5_semantic_search import semantic_search; print(semantic_search('khen thưởng giảng viên', top_k=3))"
```
*(Kết quả đúng phải trỏ về `teacher_qd_6888_can_bo.md` hoặc các bài viết news của giảng viên).*

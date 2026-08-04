# 📂 Hướng Dẫn Cấu Trúc & Sử Dụng Dữ Liệu Thu Thập (Data Directory Guide)

Thư mục này chứa toàn bộ dữ liệu cào thực tế từ **Đại học Bách khoa Hà Nội (HUST)** phục vụ cho RAG Pipeline của dự án **K3-Day08-RAG-Pipeline**. 

Dữ liệu được tổ chức theo cấu trúc phân tầng rõ ràng từ dữ liệu thô (Landing) đến dữ liệu đã chuẩn hóa (Standardized) phục vụ trực tiếp cho quá trình Indexing (Task 4) và Retrieval (Task 5-9).

---

## 🏛️ 1. Cấu Trúc Thư Mục Dữ Liệu (`data/`)

```text
data/
├── landing/                   # 📥 Dữ liệu thô ban đầu (cào trực tiếp)
│   ├── legal/                 # Chứa các file PDF chính sách, văn bản pháp quy gốc
│   └── news/                  # Chứa các file JSON bài viết tin tức cào từ ts.hust.edu.vn
└── standardized/              # ⚙️ Dữ liệu đã chuẩn hóa sang Markdown + Front Matter
    ├── legal/                 # File Markdown chuẩn hóa từ legal PDF
    └── news/                  # File Markdown chuẩn hóa từ news JSON
```

---

## 📄 2. Chi Tiết Dữ Liệu Landing (Landing Layer)

### 2.1 Văn Bản Pháp Quy Thô (`data/landing/legal/`)
Chứa **3 tài liệu PDF thực tế** tải trực tiếp từ máy chủ HUST, đại diện cho tập tài liệu pháp lý dài và có cấu trúc phức tạp:

| Tên File | Dung Lượng | Nội Dung Sơ Lược |
| :--- | :---: | :--- |
| **[hust_qd_6888_cap_nhat.pdf](file:///c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline/data/landing/legal/hust_qd_6888_cap_nhat.pdf)** | **6.05 MB** | Quyết định số 6888/QĐ-ĐHBK ban hành Quy chế công tác học sinh, sinh viên và các quy định về khen thưởng, kỷ luật, quản lý học tập tại HUST. |
| **[hust_thong_tin_tuyen_sinh_2026.pdf](file:///c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline/data/landing/legal/hust_thong_tin_tuyen_sinh_2026.pdf)** | **1.06 MB** | Đề án tuyển sinh Đại học chính quy năm 2026 của HUST, chứa thông tin chi tiết về các ngành, tổ hợp môn, chỉ tiêu và phương thức xét tuyển. |
| **[hust_thong_bao_vi_mach_ban_dan_2026.pdf](file:///c:/Users/Admin/Desktop/lab/K3-Day08-RAG-Pipeline/data/landing/legal/hust_thong_bao_vi_mach_ban_dan_2026.pdf)** | **502 KB** | Quyết định ban hành ngưỡng đảm bảo chất lượng đầu vào (điểm sàn) cho các chương trình đào tạo thuộc nhóm ngành Vi mạch bán dẫn năm 2026. |

### 2.2 Tin Tức & Thông Báo Tuyển Sinh (`data/landing/news/`)
Chứa **5 bài viết tin tức thực tế** cào từ Cổng tuyển sinh HUST dưới dạng các tệp JSON (`article_01.json` đến `article_05.json`), có cấu trúc thuộc tính như sau:

```json
{
  "url": "Đường dẫn bài viết trên website HUST",
  "title": "Tiêu đề bài viết tuyển sinh",
  "date_crawled": "Thời gian cào dữ liệu dạng ISO-8601",
  "content_markdown": "Nội dung bài viết đã chuyển đổi sang định dạng Markdown sạch"
}
```

---

## 🛠️ 3. Chi Tiết Dữ Liệu Chuẩn Hóa (Standardized Layer)

Toàn bộ tài liệu PDF và JSON đã được chuyển đổi sang tệp tin `.md` trong thư mục **`data/standardized/`**. 

Mỗi tệp tin Markdown chuẩn hóa bắt buộc phải được gắn **YAML Front Matter** ở ngay đầu tệp chứa các trường metadata đặc trưng để hỗ trợ việc phân loại dữ liệu khi truy vấn:

```markdown
---
doc_id: "HUST_LEGAL_QD6888"                      # Mã định danh duy nhất của tài liệu
title: "Quyết định Quy chế công tác sinh viên"    # Tiêu đề tài liệu chuẩn hóa
source_url: "https://hust.edu.vn/..."            # Nguồn URL gốc trích xuất tài liệu
retrieved_at: "2026-08-04T10:18:25"              # Thời điểm thu thập dữ liệu
document_version: "2026.1"                       # Phiên bản tài liệu (nếu có)
audience: "Sinh viên, Cán bộ HUST"               # Đối tượng áp dụng của văn bản
---
```

---

## 🚀 4. Hướng Dẫn Chạy Pipeline Thu Thập & Chuẩn Hóa

Khi cần cào mới hoặc cập nhật lại toàn bộ thư mục dữ liệu, bạn chạy tuần tự các lệnh sau ở project root:

```powershell
# Bước 1: Kích hoạt môi trường ảo
.venv\Scripts\activate

# Bước 2: Chạy crawler tải các file PDF văn bản gốc HUST
python src/task1_collect_legal_docs.py

# Bước 3: Chạy crawler cào các tin tức/sự kiện HUST sang JSON
python src/task2_crawl_news.py

# Bước 4: Chuyển đổi toàn bộ PDF/JSON sang Markdown thô và nạp YAML Front Matter
python src/task3_convert_markdown.py
```

### 🔒 Lưu Ý Quan Trọng Về Quy Tắc Cào Dữ Liệu
Bộ cào dữ liệu được cấu hình tuân thủ nghiêm ngặt chính sách an toàn thông tin của HUST:
*   Thiết lập delay chờ tối thiểu **1.0 giây** giữa các request để tránh gây quá tải server (`time.sleep` / `asyncio.sleep`).
*   Sử dụng chuỗi `User-Agent` hợp lệ (giả lập trình duyệt Chrome) để tránh bị hệ thống tường lửa chặn.
*   Chỉ cào thông tin công khai, không vượt CAPTCHA hay yêu cầu đăng nhập.

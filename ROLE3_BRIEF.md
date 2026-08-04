# Role 3 — Sparse Search & Advanced Reranking Dev

**Phạm vi:** Task 6 (BM25/TF-IDF) + Task 7 (RRF Reranking) + Task 8 (PageIndex Fallback) — tổng **16 điểm** trong 50 điểm bài cá nhân.

---

## 1. Bạn sở hữu 3 file

| Task | File | Điểm | Hàm phải xong |
|---|---|---|---|
| 6 | `src/task6_lexical_search.py` | 6đ | `build_bm25_index()`, `lexical_search(query, top_k) -> list[dict]` |
| 7 | `src/task7_reranking.py` | 6đ | `rerank_rrf()` (bắt buộc), `rerank()` dispatcher; `rerank_mmr` / `rerank_cross_encoder` là tuỳ chọn |
| 8 | `src/task8_pageindex_vectorless.py` | 4đ | `upload_documents()`, `pageindex_search()` |

### Contract output — KHÔNG được đổi chữ ký hàm

Role 1 sẽ `import` trực tiếp 3 file này trong `src/task9_retrieval_pipeline.py`:

```python
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search
```

- **Task 6 / Task 7** trả về `[{'content': str, 'score': float, 'metadata': dict}]`, **sort giảm dần theo `score`**.
- **Task 8** trả về thêm key `'source': 'pageindex'` (test assert đúng chuỗi này).

---

## 2. Phụ thuộc phía trước

Bạn **chỉ phụ thuộc Role 2**, và chỉ ở Task 6 & 8.

| Cần từ ai | Cần cái gì | Chặn task nào |
|---|---|---|
| Role 2 (Task 1–3) | `data/standardized/**/*.md` — hiện thư mục **đang rỗng**, chỉ có `.gitkeep` | Task 6 (corpus BM25), Task 8 (tài liệu upload) |
| Role 2 (Task 4) | `chroma_db/` + `COLLECTION_NAME = "university_services_docs"` | Task 6 *nếu* lấy corpus từ Chroma thay vì đọc `.md` |
| Role 2 (Task 5) | Schema trả về của `semantic_search()`; xác nhận `score` là **cosine similarity** (cao = tốt), không phải distance | Task 7 (RRF) + ngưỡng fallback Task 9 |
| Role 1 | `.env` có `PAGEINDEX_API_KEY` | Task 8 |

> **Task 7 không phụ thuộc ai** — RRF chỉ đọc thứ hạng, code và test được ngay với dummy data.

### Hai điều phải chốt với Role 2 ngay đầu buổi

1. **Corpus BM25 phải là đúng tập chunk đã index vào ChromaDB**, không phải file `.md` nguyên bản.
   Nếu lệch, RRF sẽ fuse hai list có `content` khác nhau về mặt chuỗi → không document nào trùng → RRF trở nên vô nghĩa.
   Cách an toàn nhất: load corpus bằng `collection.get()` từ ChromaDB (dùng chung nguồn chunk), hoặc gọi lại `chunk_documents()` của Task 4.
2. **`content` phải khớp từng ký tự** giữa dense và sparse, vì `rerank_rrf` dedupe bằng key `item["content"]`.

### Chuẩn bị trước để không bị chặn

- [ ] `pip install rank-bm25 scikit-learn pageindex` (đã có sẵn trong `requirements.txt`).
- [ ] **Đăng ký https://pageindex.ai/ và lấy API key TRƯỚC buổi lab** — đây là rủi ro lớn nhất của Role 3 (chờ email / quota).
- [ ] PageIndex **không nhận `.md`** → phải convert sang PDF bằng `fpdf2` trước khi upload. Viết sẵn hàm `md_to_pdf()`.
- [ ] Nếu Role 2 trễ dữ liệu: tự tạo 2–3 file `.md` giả trong `data/standardized/` để code & test Task 6 trước, xoá sau.

---

## 3. Thứ tự làm (khớp lịch checkpoint 180 phút)

| Mốc | Thời gian | Việc của Role 3 |
|---|---|---|
| CP2 | 0:35 – 1:00 | **Task 6** — bắt đầu ngay khi `standardized/` có file. Mục tiêu: 4 test Task 6 pass. Tranh thủ lúc chờ dữ liệu thì code trước **Task 7** (chạy được với dummy data). |
| CP3 | 1:00 – 1:20 | **Task 7** hoàn thiện + **Task 8**. Coach sẽ hỏi logic RRF & bẫy fallback. |
| CP4 | 1:20 – 1:45 | Hỗ trợ Role 1 debug fallback trong Task 9. |
| CP6 | 2:15 – 3:00 | Trả lời câu hỏi kỹ thuật về Hybrid Search / RRF / Fallback. |

Kiểm tra điểm bất cứ lúc nào:

```bash
pytest tests/test_individual.py -k "TestTask6 or TestTask7 or TestTask8" -v
```

---

## 4. Ba cái bẫy — bạn là người bị hỏi khi demo

1. **Điểm RRF không phản ánh độ liên quan.**
   Top-1 sau khi fuse luôn ≈ `1/(60+1)` ≈ `0.0164`, bất kể nội dung có liên quan hay không.
   → **Không được dùng điểm RRF làm ngưỡng fallback.** Ngưỡng phải dùng cosine gốc: `dense_results[0]["score"] < 0.48`.
   Nếu hạ threshold xuống ~0.005 cho "hợp thang RRF" thì fallback sẽ **không bao giờ** kích hoạt — kể cả query rác.

2. **API `/retrieval` của PageIndex đã deprecated.**
   Response nằm trong `retrieved_nodes[].relevant_contents` (list lồng list), và **không trả `score`** — phải tự gán theo rank.
   → `print(json.dumps(resp, indent=2))` trước khi viết parser, đừng đoán schema từ code mẫu cũ.

3. **Đổi corpus phải xoá `chroma_db/` trước khi reindex**, nếu không chunk cũ và mới lẫn lộn trong cùng collection → retrieval trả kết quả rác.

---

## 5. Điểm bonus dễ lấy (+5)

README Task 6 cho **+5 bonus nếu dùng phương pháp khác BM25 và giải thích được cơ chế trong buổi demo**.

Cách rẻ nhất: thêm `lexical_search_tfidf()` bằng `sklearn.TfidfVectorizer` (đã có trong `requirements.txt`), rồi so sánh khi demo.

**Luận điểm để trình bày:**
- TF-IDF không có **term saturation**: từ khoá lặp 50 lần được chấm điểm gấp 50 lần lặp 1 lần. BM25 thêm tham số `k1=1.5` làm điểm bão hoà dần.
- TF-IDF không **chuẩn hoá độ dài document**: document dài tự nhiên chứa nhiều từ khoá hơn nên bị ưu tiên oan. BM25 thêm `b=0.75` để phạt theo `|d|/avgdl`.
- → BM25 ổn định hơn trên corpus có độ dài lệch nhau, đúng trường hợp của ta (PDF chính sách dài vs bài tin tức ngắn).

**Bonus thêm:** đưa cả 3 ranked list (dense + BM25 + TF-IDF) vào `rerank_rrf()` để chứng minh RRF mở rộng được sang N ranker mà không cần chuẩn hoá thang điểm — đó chính là ưu điểm chính của RRF so với weighted score fusion.

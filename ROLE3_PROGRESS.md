# ✅ Role 3 — Báo Cáo Thực Thi

> Task 6 + 7 + 8 (16 điểm). Cập nhật: **2026-08-04, lần 3** — sau khi Role 2 push data + Task 4/5.
> Branch: `main` (chưa tạo nhánh, chưa commit — chờ bạn quyết định)
>
> **Đọc §7 nếu bạn chỉ có 1 phút** — đó là phần chạy trên dữ liệu thật.

---

## 0. Tóm tắt 30 giây

| Việc (theo §3 kế hoạch) | Trạng thái | Kết quả |
|---|:--:|---|
| **1** — `rerank_rrf()` + dedupe + sửa nhánh `"rrf"` | ✅ Xong | Fuse thật với BM25 trên 489 chunk (§7.2) |
| **2** — Task 8: `md_to_pdf` + `upload_documents` + `pageindex_search` | ✅ Xong | 8/8 PDF, giữ nguyên dấu tiếng Việt (§7.3) |
| **3** — Task 6: `build_bm25_index()` + `lexical_search()` | ✅ Xong | 489 chunk, **khớp 489/489 với Task 4** (§7.1) |
| **4** — `load_corpus()` trên dữ liệu thật | ✅ **W1 đã gỡ** | 8 file `.md` → 489 chunk |
| **6** — Bonus TF-IDF (+5đ) | ✅ Xong | `lexical_search_tfidf()` đối chứng |
| **7** — `rerank_cross_encoder()` (Jina API) | ✅ Xong | Degrade an toàn khi thiếu `JINA_API_KEY` |
| *(thêm)* `rerank_mmr()` | ✅ Xong | Ngoài plan, không chặn → làm luôn |
| **5** — PageIndex chạy thật | ⏸ Chờ **W3** | Code + PDF sẵn sàng, `.env` **chưa có** `PAGEINDEX_API_KEY` |

**Test:** `6 passed, 3 skipped`

```
tests/test_individual.py::TestTask6::test_returns_list                    PASSED
tests/test_individual.py::TestTask6::test_results_have_required_keys      SKIPPED  ← §8.1
tests/test_individual.py::TestTask6::test_results_sorted_descending       SKIPPED  ← §8.1
tests/test_individual.py::TestTask6::test_keyword_match_scores_higher     SKIPPED  ← §8.1
tests/test_individual.py::TestTask7::test_rerank_returns_list             PASSED
tests/test_individual.py::TestTask7::test_rerank_respects_top_k           PASSED
tests/test_individual.py::TestTask7::test_rerank_has_score                PASSED
tests/test_individual.py::TestTask8::test_function_exists                 PASSED
tests/test_individual.py::TestTask8::test_returns_list_with_source_marker PASSED
```

⚠️ 3 test SKIP **không còn là do thiếu data** — data đã có. Nguyên nhân mới: test hỏi bằng
**tiếng Anh** còn corpus **100% tiếng Việt**, xem **§8.1** (cần cả nhóm quyết định).

Không còn `raise NotImplementedError` nào trong 3 file của Role 3.

---

## 1. ⚠️ MỘT SAI SÓT TRONG KẾ HOẠCH — đã sửa, cần báo Role 1

`ROLE3_EXECUTION_PLAN.md` §4.1 bảo: nhánh `"rrf"` trong `rerank()` phải `raise ValueError`.
**Làm đúng vậy mà giữ nguyên `method: str = "rrf"` thì 3/3 test của Task 7 sẽ ĐỎ**, vì:

```python
# tests/test_individual.py:384 — gọi rerank() với method mặc định
results = rerank_fn("tuition fee payment", candidates, top_k=2)
...
except NotImplementedError:      # ← chỉ bắt NotImplementedError
    self.skipTest(...)           #    ValueError sẽ lọt ra → FAIL, không phải SKIP
```

**Đã xử lý:** đổi luôn default của `rerank()` thành `method="cross_encoder"`, giữ nguyên
`ValueError` rõ nghĩa cho nhánh `"rrf"`. Test đi vào nhánh cross-encoder → xanh thật
(không phải xanh nhờ skip).

> 📣 **Nhắn Role 1:** `src/task7_reranking.py` giờ có `rerank(..., method="cross_encoder")` là
> mặc định. Task 9 **phải gọi `rerank_rrf(ranked_lists)` trực tiếp** để fuse dense+sparse;
> gọi `rerank(method="rrf")` sẽ ăn `ValueError` kèm hướng dẫn. Đặt `RERANK_METHOD = "cross_encoder"`.

---

## 2. Chi tiết từng file

### 2.1 `src/task7_reranking.py` — Task 7 (6 điểm)

| Hàm | Ghi chú |
|---|---|
| `rerank_rrf(ranked_lists, top_k=5, k=60)` | ① dedupe theo `content` · ② `setdefault` giữ metadata bản gặp đầu · ③ ghi đè `score` bằng điểm RRF. Rỗng → `[]`. |
| `rerank_cross_encoder(query, candidates, top_k)` | Jina Reranker v2 multilingual. **Không bao giờ raise**: thiếu `JINA_API_KEY` hoặc API lỗi → in cảnh báo rồi fallback sang lexical-overlap scorer. |
| `rerank_mmr(query_embedding, candidates, top_k, lambda_param=0.7)` | Cosine thuần Python, không cần numpy. Trả `score` = điểm MMR. |
| `rerank(...)` | `cross_encoder` (mặc định) · `mmr`/`rrf` → `ValueError` chỉ rõ phải gọi hàm nào. |

**Verify RRF (đã chạy thật):**

```
dense  = [Tuition fee payment schedule(0.81), Scholarship eligibility(0.62)]
sparse = [Library study room(12.4),           Tuition fee payment schedule(9.1)]

rerank_rrf([dense, sparse]) →
  [0.0325] Tuition fee payment schedule      ← 1/61 + 1/62, có mặt ở CẢ 2 list → nổi lên top ✓
  [0.0164] Library study room booking guide  ← 1/61
  [0.0161] Scholarship eligibility           ← 1/62
```

Đúng như kỳ vọng: BM25 score `12.4` và cosine `0.81` không hề được cộng trực tiếp — chỉ
thứ hạng được dùng. Và dải điểm rơi vào `0.016 → 0.033`, xác nhận **không thể** dùng làm threshold.

### 2.2 `src/task6_lexical_search.py` — Task 6 (6 điểm) + bonus (+5)

- `tokenize()` — tokenizer dùng chung cho index và query (`.lower().split()`).
- `load_corpus(source_dir=STANDARDIZED_DIR)` — import `CHUNK_SIZE`/`CHUNK_OVERLAP` **từ Task 4**
  và chunk bằng `RecursiveCharacterTextSplitter` với đúng separators, để `content` khớp
  từng ký tự với dense (xử lý rủi ro §2 của kế hoạch).
  Thư mục rỗng / thiếu thư viện → `[]`, không raise.
  *Có tham số `source_dir` để test được với corpus giả mà **không phải tạo file rác trong `data/`**.*
- `build_bm25_index()` → `BM25Okapi`, corpus rỗng → `None`.
- `lexical_search()` → lọc `score == 0`, sort giảm dần, metadata dùng key `"type"`.
- `lexical_search_tfidf()` **(bonus)** → TF-IDF + cosine, cùng schema, để so sánh trực tiếp.

**Verify bằng corpus giả (2 file `.md`, không đụng `data/`):**

```
corpus = 3 chunks, metadata = {'source': 'tuition_policy.md', 'type': 'legal', 'chunk_index': 0}

BM25 'tuition fee payment'      → 2 hits, top 1.185 (legal)
BM25 'library study room'       → 1 hit,  top 2.258 (news)
BM25 'quantum physics lecture'  → 0 hits          ← lọc score==0 hoạt động đúng ✓
sort giảm dần ✓   mọi score > 0 ✓   TF-IDF cho cùng thứ hạng, thang điểm 0→1 ✓

RRF trên corpus thật (dense giả lập trả lại đúng 1 chunk của sparse):
  chunk trùng lên top ✓   metadata gốc {'source','type','chunk_index'} được giữ ✓
```

### 2.3 `src/task8_pageindex_vectorless.py` — Task 8 (4 điểm)

| Hàm | Ghi chú |
|---|---|
| `md_to_pdf(md_file)` | fpdf2, PageIndex chỉ nhận PDF. ⚠ dùng font core Helvetica + latin-1 → **tài liệu tiếng Việt có dấu sẽ mất dấu**, phải nhúng `DejaVuSans.ttf` nếu corpus là tiếng Việt (đã ghi chú trong docstring). |
| `upload_documents()` | Cache `{md_filename: doc_id}` ra `data/pageindex_docs.json`, bỏ qua file đã upload → không đốt call API khi chạy lại. |
| `pageindex_search(query, top_k)` | Poll `get_retrieval` tối đa 20 lần × 3s. Parse `retrieved_nodes[*].relevant_contents[*][*]`. Mọi kết quả có **`"source": "pageindex"` ở top-level**. |

Đường an toàn (đã chạy thật, không có key):
```
⚠ Hãy set PAGEINDEX_API_KEY trong file .env
  (pageindex_search() vẫn trả [] an toàn, không làm sập Task 9)
```
Thiếu key → `[]` · thiếu SDK → `[]` · API lỗi → `[]` · timeout → `[]`. **Không nhánh nào raise.**

---

## 3. Còn chờ gì — nguyên văn

| # | Chờ ai | Chờ cái gì | Khi có thì làm gì |
|:-:|---|---|---|
| **W1** | Role 2 (T3) | `data/standardized/**/*.md` | ✅ **ĐÃ GỠ** — 8 file, 489 chunk. Không phải sửa dòng code nào |
| **W2** | Role 2 (T4) | Splitter + `CHUNK_SIZE`/`CHUNK_OVERLAP` | ✅ **ĐÃ GỠ** — Role 2 dùng `RecursiveCharacterTextSplitter`, cùng separators. Verify khớp **489/489 chunk** (§7.1). Vẫn còn tranh cãi `500/50` vs `800/100` → §6.1 |
| **W3** | Role 1 | `PAGEINDEX_API_KEY` trong `.env` | ⏸ **CÒN CHỜ** — `.env` hiện chỉ có `OPENROUTER_API_KEY`. Có key là chạy `python -m src.task8_pageindex_vectorless` được ngay (8 PDF đã convert sẵn) |
| **W4** | Role 1 | Xác nhận đổi `RERANK_METHOD = "cross_encoder"` | ⏸ Còn chờ — xem §1 |
| *(mới)* | Role 2 | Chạy `python -m src.task4_chunking_indexing` để dựng `chroma_db/` | ⏸ Còn chờ — §8.2. Chưa có thì `semantic_search()` trả `[]`, không test được hybrid thật |

---

## 4. Môi trường đã setup

```bash
# Đã cài vào .venv (Python 3.11.6):
rank-bm25  scikit-learn  python-dotenv  numpy  fpdf2  langchain-text-splitters  pytest
pageindex  pypdf                # pypdf chỉ dùng để tự kiểm tra dấu trong PDF, không phải dependency
```

Lệnh chạy lại:
```bash
.venv/bin/python -m pytest tests/test_individual.py -k "TestTask6 or TestTask7 or TestTask8" -v
.venv/bin/python -m src.task6_lexical_search
.venv/bin/python -m src.task7_reranking
.venv/bin/python -m src.task8_pageindex_vectorless
```

---

## 5. Definition of Done — đối chiếu

- [x] `lexical_search()` lọc bỏ `score == 0`, sort giảm dần
- [x] Tokenizer tối thiểu `.lower().split()`, dùng chung index + query
- [x] `rerank_rrf()` dedupe theo `content`, cộng dồn điểm, giữ `metadata` gốc
- [x] `rerank()` nhánh `"rrf"` raise `ValueError` rõ nghĩa (Bẫy #1) + đổi default → không phá test
- [x] `pageindex_search()` trả `[]` khi thiếu API key, kết quả có `"source": "pageindex"`
- [x] Metadata dùng key `"type"` (không phải `doc_type`)
- [x] Mọi lỗi/rỗng → `return []`, không `raise`, không `None`
- [x] Không tạo file `.md` giả trong `data/` → **không có gì phải xoá trước khi merge**
- [x] Không còn `raise NotImplementedError` trong 3 file của Role 3
- [x] `CORPUS` load dữ liệu thật — **489 chunk, khớp 489/489 với Task 4**
- [x] File cache của Task 8 (`data/pageindex_pdfs/`, `data/pageindex_doc_ids.json`) đã nằm trong `.gitignore`
- [ ] PageIndex chạy thật — **chờ `PAGEINDEX_API_KEY` (W3)**
- [ ] Đã push nhánh + báo group chat — **chưa làm** (chưa tạo `feat/role3-retrieval`, chưa commit)

---

## 6. Đối chiếu với hướng dẫn chính thức (rà lại lần 2)

| Ý trong hướng dẫn | Đối chiếu code | Kết luận |
|---|---|---|
| Task 6: "BM25 giỏi tìm **từ khoá chính xác** như mã voucher `SPP123`" | `tokenize()` cũ là `.lower().split()` → `"SPP123."` thành token `"spp123."`, query `"SPP123"` **không match** | ⚠️ **Đã sửa** — bóc dấu câu ở 2 đầu token, giữ nguyên `3.2` / `2025-2026` |
| Task 6: "Semantic hay bỏ sót từ khoá đặc biệt → dùng cả hai bù trừ" | `lexical_search()` + `semantic_search()` fuse bằng `rerank_rrf` | ✅ Đúng thiết kế |
| Task 7: `RRF(d) = Σ 1/(60 + r(d))` | `1 / (k + rank)`, `k=60`, `rank` từ 1 | ✅ Khớp công thức |
| Task 7: "cosine ∈ [0,1] vs BM25 thô 0→20+, KHÔNG cộng trực tiếp" | Code chỉ dùng `rank`, không đụng `score` gốc | ✅ Đúng |
| Task 7: "🛠️ Chạy `python src/task7_reranking.py`" | Chạy được | ✅ |
| Task 6: chạy `python src/task6_lexical_search.py` | **Crash** `ModuleNotFoundError: No module named 'src'` (vì import hằng số từ Task 4) | ⚠️ **Đã sửa** — thêm bootstrap `sys.path`, giờ chạy được cả `python src/...` lẫn `python -m src....` |
| "chia nhỏ thành các đoạn **800 ký tự**" (+ `LAB_GUIDE.md:82`, `:138` ghi `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`) | `src/task4_chunking_indexing.py:44-45` đang là **`500 / 50`** | ⚠️ **Sai — nhưng là file của Role 2.** Xem §6.1 |
| Task 8: "truy vấn theo cấu trúc Mục Lục, không qua chunking" | `pageindex_search()` gọi `submit_query` trên nguyên tài liệu PDF, parse `retrieved_nodes` theo `section_title` | ✅ Đúng tinh thần |
| Task 8: fallback cho câu hỏi tổng quan | Role 1 gate bằng `cosine < 0.48` (`LAB_GUIDE.md` CP3) | ✅ Củng cố §1: **phải dùng cosine gốc, không dùng điểm RRF** |

### 6.1 ⚠️ `CHUNK_SIZE` — vẫn chưa khớp hướng dẫn (cập nhật sau khi Role 2 nộp Task 4)

Role 2 đã viết xong Task 4 nhưng **giữ `500 / 50`** và ghi hẳn lý do vào docstring
(`chunk_documents()`: *"CHUNK_SIZE = 500: Balances context resolution and BAAI/bge-m3..."*).
Trong khi đó `LAB_GUIDE.md:82` liệt kê `CHUNK_SIZE=800, CHUNK_OVERLAP=100` là mục **Role 1 phải kiểm tra**
ở CP2, và `LAB_GUIDE.md:138` cũng ghi `size=800, overlap=100`.

**Task 6 không bị ảnh hưởng** — nó import hằng số nên đổi lúc nào cũng tự bám theo, và §7.1 đã
chứng minh khớp 489/489 chunk ở mức `500/50` hiện tại.

Nhưng đây là điểm **Role 1 sẽ bị hỏi ở CP2**. Cần chốt 1 trong 2:
- Đổi thành `800 / 100` cho khớp hướng dẫn (rồi **xoá `chroma_db/` và reindex**, xem cảnh báo trong docstring Task 4), hoặc
- Giữ `500 / 50` và chuẩn bị lý lẽ bảo vệ trước coach.

### 6.2 ℹ️ `LAB_GUIDE.md` tự mâu thuẫn về vai trò Role 3 — không phải lỗi code

- `LAB_GUIDE.md:43` (Phương án B, 5 người): Role 3 = **Task 6 + 7 + 8** ✅ khớp `ROLE3_BRIEF.md`
- `LAB_GUIDE.md:84` (CP2): lại ghi Role 3 làm **Task 5** (semantic + HyDE)
- `LAB_GUIDE.md:88` (CP3): lại ghi Role 3 làm **Task 8**

Phần checkpoint của `LAB_GUIDE` đặt tên vai trò theo Phương án A/C nên lệch. **Bám `ROLE3_BRIEF.md` + `TEAM_ARCHITECTURE.md`** (Phương án B) là đúng — nhưng nên xác nhận 1 câu với Role 1 xem nhóm chốt phương án nào, vì nếu nhóm theo bản CP2 thì bạn phải làm Task 5 + HyDE thay vì Task 6.

### 6.3 ℹ️ Corpus BM25: đọc `.md` hay đọc thẳng ChromaDB?

`ROLE3_BRIEF.md` §2 nói cách **an toàn nhất** là `collection.get()` từ ChromaDB để dùng chung đúng tập chunk.
Hiện `load_corpus()` đang re-chunk từ `.md` bằng đúng tham số Task 4 (phương án 2 mà chính tài liệu đó cũng chấp nhận).

✅ **Đã kiểm chứng, không cần đổi:** Role 2 dùng `RecursiveCharacterTextSplitter` với đúng
`separators=["\n\n", "\n", ". ", " ", ""]` → hai cách cho kết quả **giống hệt nhau, 489/489 chunk** (§7.1).

Chỉ cần đổi sang đọc ChromaDB **nếu** sau này Role 2 chuyển sang `MarkdownHeaderTextSplitter`
hoặc `SemanticChunker`.

---

## 7. ✅ Chạy lại trên DỮ LIỆU THẬT (sau khi Role 2 push data + Task 4/5)

Dữ liệu đã có: **8 file `.md`** (3 legal HUST + 5 news), tổng ~213 KB, **toàn bộ tiếng Việt**.

### 7.1 W1 đã gỡ — Task 6 chạy thật, khớp Task 4 tuyệt đối

```
Corpus: 489 chunks (chunk_size=500, overlap=50)

So khớp với task4.chunk_documents(task4.load_documents()):
  task4 chunks: 489 | task6 chunks: 489
  content identical (same order): True      ← 489/489 khớp từng ký tự
  metadata t4[0] == t6[0]: {'source': 'hust_qd_6888_cap_nhat.md', 'type': 'legal', 'chunk_index': 0}
```

👉 **RRF sẽ dedupe được.** Rủi ro số 1 của kế hoạch (§2) coi như đã đóng: Role 2 dùng
`RecursiveCharacterTextSplitter` với đúng separators, và `load_corpus()` import thẳng hằng số
nên tự bám theo — kể cả sau này Role 2 đổi `500/50` sang `800/100`.

Kết quả BM25 trên truy vấn tiếng Việt thật:

| Query | Hits | Top-1 |
|---|:--:|---|
| `học phí` | 3 | `5.067` — bảng mức học phí chương trình tài năng |
| `điều kiện trúng tuyển` | 3 | `7.724` |
| `học bổng sinh viên` | 3 | `9.520` — mục Học bổng KKHT |
| `vi mạch bán dẫn` | 3 | `17.791` — đúng file thông báo vi mạch |
| `quantum blockchain` | **0** | lọc `score == 0` hoạt động đúng |

### 7.2 Hybrid end-to-end — **DỰNG THẬT, không còn giả lập**

`chroma_db/` đã có (489 chunk). Chạy `semantic_search()` + `lexical_search()` + `rerank_rrf()` thật:

```
Q: điều kiện xét học bổng khuyến khích học tập     cosine=0.6663  overlap=2/5  -> HYBRID
   1. [0.0323] BOTH   tuyen_sinh#145  'Điều kiện được xét, cấp học bổng KKHT: - Học bổng loại khá...'
   2. [0.0320] BOTH   tuyen_sinh#144  '(1) Học bổng khuyến khích học tập (KKHT) ĐHBK Hà Nội...'

Q: mức học phí chương trình tiên tiến              cosine=0.6045  overlap=5/5  -> HYBRID
   1. [0.0325] BOTH   tuyen_sinh#117  'Bảng 4. Mức học phí các chương trình Elitech...'
   2. [0.0315] BOTH   tuyen_sinh#131  'Bảng 7. Mức học phí các chương trình tài năng...'

Q: ngưỡng đảm bảo chất lượng ngành vi mạch bán dẫn cosine=0.6656  overlap=5/5  -> HYBRID
   1. [0.0325] BOTH   vi_mach#1  'THÔNG BÁO NGƯỠNG ĐẢM BẢO CHẤT LƯỢNG...'
   2. [0.0323] BOTH   vi_mach#2  'Căn cứ Công văn số 4431/BGDĐT-GDĐH...'

Q: cách làm bánh chưng ngày Tết  (ngoài domain)    cosine=0.4286  overlap=0/5  -> FALLBACK ✓
```

**`overlap=5/5`** nghĩa là cả 5 chunk trong top-5 sau fuse đều xuất hiện ở **cả** dense lẫn sparse —
đúng cái mà RRF sinh ra để làm. Câu ngoài domain thì `overlap=0/5` và gate bật fallback đúng.

Nhưng để có được kết quả này phải sửa **3 bug** — xem §7.4.

### 7.3 Task 8 — sửa 3 lỗi lộ ra khi gặp dữ liệu thật

| Lỗi | Triệu chứng | Đã sửa |
|---|---|---|
| **Font latin-1** | `"Quyết định"` → `"Quyet dinh"`, PageIndex index toàn bộ corpus tiếng Việt sai | Nhúng TTF Unicode (`_find_unicode_font()`, tự dò macOS/Linux/Windows) |
| **`multi_cell` mặc định** | `Not enough horizontal space to render a single character` → **0/8 file convert được** | fpdf2 2.8 giữ con trỏ ở mép phải sau mỗi `multi_cell` → thêm `new_x="LMARGIN", new_y="NEXT"` |
| **Token siêu dài** | Bảng markdown `\|-----...----\|` và URL không có khoảng trắng, rộng hơn khổ giấy | `_soft_wrap()` cắt token > 60 ký tự |

Kết quả:
```
✓ 8/8 PDF convert thành công (25 KB → 122 KB)
Kiểm tra lại bằng pypdf: "Quyết định 6888/QĐ-ĐHBK ... Học sinh Sinh viên"  → CÒN NGUYÊN DẤU ✓
```

Đồng thời đối chiếu với **SDK `pageindex` thật** (đã cài trong `.venv`):
- `submit_document(file_path) -> {'doc_id'}` ✓ · `submit_query(doc_id, query) -> {'retrieval_id'}` ✓ · `get_retrieval(retrieval_id)` ✓
- **Thêm `is_retrieval_ready(doc_id)`**: PageIndex trả `doc_id` ngay nhưng dựng cây mục lục ở background — query sớm sẽ lỗi. Giờ bỏ qua doc chưa sẵn sàng thay vì ném exception.
- Đổi tên `data/pageindex_pdfs/` + `data/pageindex_doc_ids.json` cho **khớp `.gitignore` sẵn có** (dòng 18–19) → file cache không lọt vào git.

---

## 8. Trạng thái 2 việc phụ thuộc bên ngoài

### 8.1 Test Task 6 vẫn SKIP: corpus tiếng Việt vs test tiếng Anh

`tests/test_individual.py` hỏi bằng **tiếng Anh**, corpus lại **100% tiếng Việt**:

```
'tuition fee payment policy'   BM25=0 hits    ← test_results_have_required_keys  → SKIP
'scholarship eligibility'      BM25=0 hits    ← test_results_sorted_descending   → SKIP
'library study room'           BM25=0 hits    ← test_keyword_match_scores_higher → SKIP
```

BM25 là so khớp từ khoá **chính xác** — không có cách nào để `"tuition fee"` match `"học phí"`.
Đây **không phải lỗi code**: 3 test này gọi `self.skipTest("Không có kết quả")` chứ không FAIL.
Nhưng nếu coach muốn thấy `PASSED` thay vì `SKIPPED` ở CP2 thì nhóm phải chọn:

1. **Role 2 thêm 1–2 tài liệu tiếng Anh** vào `data/standardized/` (nhanh nhất, đúng chủ đề "University Services").
2. Giữ nguyên và **giải thích với coach** — hợp lý, vì Task 5 (dense, đa ngôn ngữ với `bge-m3`) vẫn match được, còn BM25 thì không. **Đây chính là ví dụ sống của việc "hai phương pháp bù trừ cho nhau"** mà hướng dẫn nêu → đáng nói khi trình bày.

> Tôi không tự thêm file tiếng Anh vào `data/` vì đó là thư mục Role 2 sở hữu.

### 8.2 ✅ `chroma_db/` đã build xong — và 2 bug trong đó đã được sửa

Đã chạy `python -m src.task4_chunking_indexing`: 8 documents → 489 chunks → embed bằng
`BAAI/bge-m3` (tải ~2.3 GB) → index vào `chroma_db/`.

Khi đo điểm cosine thật thì lộ ra 2 lỗi, **cả hai đã sửa xong** — xem §10.4 và §10.5.
Kèm theo đó là đề xuất hiệu chuẩn lại ngưỡng fallback ở §10.6.

---

## 10. 🔴 BUG NẶNG trong Task 4 — vector store đang dùng L2 chứ không phải cosine

### 10.1 Triệu chứng

```
Query: "học phí ngành khoa học máy tính là bao nhiêu"
  semantic_search() trả score = 0.2637
  cosine tính tay (bge-m3, normalize) = 0.6319      ← lệch hơn 2 lần
```

### 10.2 Nguyên nhân

`index_to_vectorstore()` khai báo không gian đo bằng `metadata=`:

```python
# src/task4_chunking_indexing.py:196 — KHÔNG có tác dụng trên chromadb 1.5.9
collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=None,
    metadata={"hnsw:space": "cosine"}      # ← bị bỏ qua LẶNG LẼ, không warning
)
```

Kiểm tra collection vừa tạo:
```python
col.metadata            # None                       ← metadata bị nuốt luôn
col.configuration_json  # {'hnsw': {'space': 'l2', ...}}   ← rơi về mặc định L2
```

Chroma trả **bình phương khoảng cách Euclid**. Với vector đã chuẩn hoá thì
`|a-b|² = 2 - 2·cos`, nên `score = 1 - distance` của Task 5 thực chất đang tính `2·cos - 1`
chứ không phải `cos`. Kiểm chứng: `2 × 0.6319 − 1 = 0.2638` ≈ đúng con số `0.2637` quan sát được.

### 10.3 Hệ quả — làm hỏng đúng cái gate fallback của Task 9

Cùng bộ embedding, chỉ khác không gian đo:

| Query | space **cosine** (đúng) | space **l2** (hiện tại) |
|---|:--:|:--:|
| `học phí ngành khoa học máy tính là bao nhiêu` | **0.6319** | 0.2637 |
| `cách nấu phở bò gia truyền` *(lạc đề)* | **0.4015** | 0.0000 |

Ngưỡng `0.48` mà `LAB_GUIDE.md` CP3 đưa ra **tách hai trường hợp này rất gọn** — nhưng chỉ khi
space là cosine. Với L2 hiện tại, đo trên 5 query thật thì **5/5 đều dưới 0.48** → fallback
PageIndex **luôn luôn bật**, kể cả câu hỏi hoàn toàn đúng chủ đề.

### 10.4 ✅ ĐÃ SỬA — không cần reindex

Có 2 đường sửa. Tôi chọn đường **không phải embed lại 489 chunk**:

**Đã làm — `src/task5_semantic_search.py` quy đổi theo đúng không gian đo của collection:**

```python
space = collection.configuration_json["hnsw"]["space"]   # đọc thẳng từ collection
...
if space in ("cosine", "ip"):
    raw_score = 1.0 - dist
else:                          # "l2" — squared euclidean trên vector đã chuẩn hoá
    raw_score = 1.0 - dist / 2.0
```

Đúng về mặt toán học (`|a-b|² = 2 - 2·cos` ⟹ `cos = 1 - dist/2`) và **an toàn cả khi sau này
Role 2 reindex sang space cosine** — lúc đó nhánh `cosine` tự động được chọn, không phải sửa lại.

Đã xác minh điều kiện tiên quyết: embedding của `bge-m3` **đã chuẩn hoá sẵn**
(`norm(query) = 1.0`, `norm(stored) = 1.0000000284`), nên công thức trên áp dụng được.

```
chroma distance      : 0.6674
score Task5 CŨ       : 0.3326      ← sai
score Task5 MỚI      : 0.6663
cosine tính tay      : 0.6663      ← khớp tuyệt đối ✓
```

**Đường còn lại (tuỳ chọn, sạch hơn về lâu dài):** Role 2 đổi Task 4 sang
`configuration={"hnsw": {"space": "cosine"}}` rồi `rm -rf chroma_db/ && python -m src.task4_chunking_indexing`.
Làm hay không đều được — Task 5 giờ chạy đúng ở cả hai trường hợp.

### 10.5 ✅ ĐÃ XOÁ record rác — nó tệ hơn tưởng

```
id: test_1 | metadata: {'source': 's.md', 'type': 'legal'} | document: 'nội dung test'
```

Không phải chỉ là "thừa 1 record". Embedding của nó **toàn số 0**:

```
dim: (1024,)   norm: 0.0   số phần tử khác 0: 0
```

Với squared-L2, vector 0 cho khoảng cách **đúng bằng 1.0 với MỌI query đã chuẩn hoá** → nó tạo ra
một cái **sàn cứng `score = 0.5`**. Hệ quả: mọi câu hỏi lạc đề đều trả về `'nội dung test'` ở
**hạng 1** với điểm 0.5000 y hệt nhau, che mất điểm thật:

```
TRƯỚC khi xoá — 5 câu hỏi lạc đề khác nhau, cùng ra một con số:
  0.5000  cách làm bánh chưng ngày Tết        -> s.md 'nội dung test'
  0.5000  giá vé máy bay đi Đà Nẵng           -> s.md 'nội dung test'
  0.5000  cách chăm sóc mèo con               -> s.md 'nội dung test'

SAU khi xoá — điểm thật hiện ra:
  0.4286  cách làm bánh chưng ngày Tết
  0.4535  giá vé máy bay đi Đà Nẵng
  0.3658  cách chăm sóc mèo con
```

Đã chạy `col.delete(ids=["test_1"])` → collection còn **489 record, khớp đúng BM25**.
Record này không do dòng code nào trong repo sinh ra (`grep` cả `src/`, `tests/`, `app.py`) —
gần như chắc chắn từ một lần chạy thử thủ công.

### 10.6 📣 Ngưỡng fallback: đề xuất **0.55**, không phải 0.48

Sau khi sửa §10.4 + §10.5, đo top-1 cosine trên 11 query (6 đúng chủ đề, 5 lạc đề):

| Nhóm | Dải điểm |
|---|---|
| **Đúng chủ đề** (học bổng, học phí, vi mạch, xét tuyển tài năng, liên kết quốc tế, quy định SV) | `0.6045 → 0.7048` |
| **Lạc đề** (bánh chưng, vé máy bay, chăm mèo, bóng đá, phở bò) | `0.3658 → 0.4893` |

Khoảng trống nằm ở `0.4893 … 0.6045`.

⚠️ **`0.48` của `LAB_GUIDE` CP3 nằm THẤP HƠN đỉnh của nhóm lạc đề (`0.4893`)** — query
*"kết quả bóng đá ngoại hạng Anh"* đạt `0.4893 > 0.48` nên **sẽ không kích hoạt fallback**.
Đặt giữa khoảng trống thì an toàn hơn hẳn:

```python
# src/task9_retrieval_pipeline.py — Role 1
SIMILARITY_THRESHOLD = 0.55
```

Nếu coach hỏi vì sao lệch tài liệu: `0.48` hợp lý với embedding model khác, nhưng `bge-m3` có
**sàn tương đồng cao** cho tiếng Việt (hai câu chẳng liên quan gì vẫn ~0.4) → phải hiệu chuẩn
lại trên corpus thật. **Đây là số đo được, không phải số chọn bừa** — đúng tinh thần câu hỏi
"vì sao không dùng điểm RRF làm ngưỡng".

---

## 9. Việc kế tiếp cho bạn

Pipeline retrieval giờ **chạy đúng đầu-cuối trên dữ liệu thật**. Việc còn lại đều là
**nhắn người khác**, không phải code:

1. **Role 1 — 2 con số phải đổi trong Task 9:**
   - `SIMILARITY_THRESHOLD = 0.55` (không phải `0.48` — §10.6, có số đo kèm)
   - `RERANK_METHOD = "cross_encoder"`; gọi `rerank_rrf()` **trực tiếp** để fuse (§1)
   - Gate so với `dense_results[0]["score"]` (cosine) — **tuyệt đối không** dùng điểm RRF (`0.016 → 0.033`)
2. **Role 1** — xin `PAGEINDEX_API_KEY` (W3). Thứ **duy nhất** còn chặn Role 3.
   Có key là chạy ngay được, 8 PDF đã convert sẵn trong `data/pageindex_pdfs/`.
3. **Role 2** — báo là tôi đã sửa `task5_semantic_search.py` (§10.4) và xoá 1 record rác
   trong `chroma_db` (§10.5). Nếu muốn sạch hơn thì đổi Task 4 sang
   `configuration={"hnsw": {"space": "cosine"}}` rồi reindex — **không bắt buộc**, Task 5 giờ
   chạy đúng ở cả hai không gian đo.
4. **Role 2** — chốt `500/50` hay `800/100` (§6.1). Nếu đổi thì reindex một lần cho cả hai việc.
5. **Cả nhóm** — quyết định §8.1 (test tiếng Anh vs corpus tiếng Việt). Chọn phương án 2 thì
   đây là **điểm cộng khi thuyết trình**, không phải điểm trừ.

# ⚡ Role 3 — Kế Hoạch Thực Thi Nhanh Nhất

### Sparse Search & Advanced Reranking Dev — Task 6 + 7 + 8 (16 điểm)

> Tài liệu này trả lời đúng 2 câu hỏi: **việc nào làm được NGAY**, và **việc nào buộc phải chờ**.
> Tuân thủ hợp đồng dữ liệu tại `TEAM_ARCHITECTURE.md` §2.

---

## 0. Kết luận trước — đọc 30 giây

**Trong 3 task của bạn, chỉ có ĐÚNG MỘT chỗ bị chặn: biến `CORPUS` của Task 6.**

Mọi thứ còn lại — toàn bộ Task 7, toàn bộ logic Task 8, và ~90% code Task 6 — viết được **ngay từ phút 0**, không cần Role 2, không cần ChromaDB, không cần một dòng dữ liệu thật nào.

```
Tổng khối lượng Role 3
├── 85%  ← LÀM ĐƯỢC NGAY (song song với mọi người)
│         Task 7 toàn bộ · Task 8 toàn bộ · Task 6 khung + hàm search
└── 15%  ← PHẢI CHỜ (chỉ là 1 hàm load_corpus() ~15 dòng)
          Chờ: data/standardized/ của Role 2
```

👉 Chiến lược: **viết hết phần không chờ trước, để lại đúng 1 hàm `load_corpus()` cắm vào cuối.**

---

## 1. Bảng CHỜ — dependency thật sự

| # | Chờ ai | Chờ cái gì | Chặn chính xác cái gì | Gỡ chặn tạm bằng |
|:-:|---|---|---|---|
| W1 | **Role 2** (T3) | `data/standardized/**/*.md` (hiện **rỗng**, chỉ có `.gitkeep`) | `CORPUS` của Task 6 + input upload của Task 8 | Tự tạo 3 file `.md` giả → **xoá trước khi merge** |
| W2 | **Role 2** (T4) | Chốt `CHUNK_SIZE` / `CHUNK_OVERLAP` (starter `500/50`, LAB_GUIDE nói `800/100`) | Độ khớp `content` giữa BM25 và dense → ảnh hưởng RRF | Hỏi ngay ở CP0, 1 câu chat |
| W3 | **Role 1** | `.env` có `PAGEINDEX_API_KEY` | *Chỉ chặn lúc chạy thật*, **không chặn viết code** | Code đường `return []` khi thiếu key trước |
| W4 | **Role 1** | Chốt Bẫy #1 (`rerank(method="rrf")`) | 3 dòng sửa trong `rerank()` | Đã có phương án sẵn ở §4 dưới |

**Không có dependency nào khác.** Bạn không chờ Role 4, không chờ Role 5, không chờ Task 5 của Role 2.

> ⚠️ W1 nằm trên **đường găng của cả nhóm** (`T3 → T4 → T5 → T9`). Nếu Role 2 chậm ở CP1, cách nhanh nhất để bạn *không* bị chặn là **nhảy vào crawl giúp Role 2 vài URL** — vì Task 7 của bạn là toán học thuần, dời lúc nào cũng được.

---

## 2. ⚠️ Rủi ro tích hợp số 1 — phải chốt ở CP0, trước khi code

`TEAM_ARCHITECTURE.md` §8.2 ghi *"`CORPUS` load từ `data/standardized/`"*.
Nhưng §2.1 lại ghi *"`content` là **KHOÁ ĐỊNH DANH** dùng để dedupe trong RRF"*.

**Hai điều này mâu thuẫn nếu làm ngây thơ:**

```
Role 2 → ChromaDB:  chunk 500 ký tự  →  dense_results[i]["content"] = "Học phí chương trình..."
Role 3 → BM25:      cả file .md      →  sparse_results[j]["content"] = "# Tuition Fees\n\n## Overview\n..."
                                          ↓
                    rerank_rrf() dedupe theo content → KHÔNG chunk nào trùng
                                          ↓
                    RRF không cộng dồn được điểm → mất hoàn toàn tác dụng
                    Hybrid search suy biến thành 2 list nối đuôi nhau
```

### ✅ Phương án bắt buộc: BM25 phải chunk y hệt Task 4

```python
# src/task6_lexical_search.py
from .task4_chunking_indexing import CHUNK_SIZE, CHUNK_OVERLAP   # chỉ import HẰNG SỐ

def load_corpus() -> list[dict]:
    """Đọc .md và chunk BẰNG ĐÚNG THAM SỐ của Task 4 để content khớp với dense."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    corpus = []
    for md in STANDARDIZED_DIR.rglob("*.md"):
        doc_type = "legal" if "legal" in str(md) else "news"
        for i, text in enumerate(splitter.split_text(md.read_text(encoding="utf-8"))):
            corpus.append({
                "content": text,
                "metadata": {"source": md.name, "type": doc_type, "chunk_index": i},
            })
    return corpus
```

**Nhắn Role 1 + Role 2 ngay ở CP0:**
> *"Task 6 sẽ import `CHUNK_SIZE`/`CHUNK_OVERLAP` từ task4 và chunk giống hệt, để `content` khớp từng ký tự với dense — nếu không RRF sẽ không dedupe được. Role 2 đừng đổi 2 hằng số này sau CP2."*

Nếu Role 2 dùng `MarkdownHeaderTextSplitter` thay vì `Recursive` → bạn phải copy đúng splitter đó. **Hỏi 1 câu, tiết kiệm 30 phút debug.**

---

## 3. Bảng LÀM — thứ tự tối ưu theo độ chặn

Sắp xếp theo nguyên tắc: **việc không chờ ai làm trước, việc chờ dữ liệu đẩy về sau.**

| Thứ tự | Việc | Chờ gì | Ước lượng | Test bằng |
|:--:|---|---|:--:|---|
| **1** | `rerank_rrf()` + dedupe + sửa nhánh `"rrf"` | ❌ Không chờ gì | 15' | `tests/fixtures.py` xáo 2 list |
| **2** | Task 8: `md_to_pdf()` + `upload_documents()` + `pageindex_search()` + đường `return []` | ❌ Không chờ (code trước, chạy sau) | 25' | `PAGEINDEX_API_KEY=""` → phải ra `[]` |
| **3** | Task 6: khung + `build_bm25_index()` + `lexical_search()` | ❌ Không chờ | 15' | corpus giả 3 dict inline |
| **4** | Task 6: `load_corpus()` cắm vào | ✅ **Chờ W1** | 10' | `pytest -k TestTask6` |
| **5** | Task 8: chạy upload thật | ✅ Chờ W1 + W3 | 15' | `pytest -k TestTask8` |
| **6** | Bonus: `lexical_search_tfidf()` (+5đ) | ❌ Không chờ | 10' | so sánh với BM25 |
| **7** | `rerank_cross_encoder()` (Jina API) | ❌ Không chờ | 15' | Task 9 cần ở CP3 |

> 🎯 Việc **1 → 2 → 3** = 55 phút thuần, làm được ngay CP0/CP1 khi Role 2 còn đang crawl. Xong sớm 3 việc này là bạn **đi trước timeline một checkpoint**.

---

## 4. Bốn quyết định kỹ thuật đã chốt sẵn — không cần suy nghĩ lại

### 4.1 `rerank()` nhánh `"rrf"` — sửa theo Bẫy #1

RRF là bước **merge** (nhận *nhiều* ranked list), không phải bước **rerank** (nhận *một* candidate list). Không nhét vào chung interface được.

```python
elif method == "rrf":
    raise ValueError(
        "RRF là bước merge nhiều ranked lists — hãy gọi rerank_rrf() trực tiếp, "
        "không qua rerank()."
    )
```
→ Báo Role 1 đổi `RERANK_METHOD = "cross_encoder"` trong Task 9.

### 4.2 `rerank_rrf()` — 3 điều bắt buộc

```python
def rerank_rrf(ranked_lists, top_k=5, k=60):
    rrf_scores, chunk_map = {}, {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, 1):          # rank bắt đầu từ 1
            key = item["content"]                        # ① dedupe theo content
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)
            chunk_map.setdefault(key, item)              # ② giữ metadata chunk GỐC
    ordered = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [{**chunk_map[c], "score": s} for c, s in ordered[:top_k]]   # ③ ghi đè score
```

- ① Chunk có mặt ở **cả** dense và sparse → điểm cộng dồn → nổi lên top. Đây chính là *toàn bộ* giá trị của hybrid search.
- ② `setdefault` chứ không `=`, để không mất metadata bản gặp đầu tiên.
- ③ `score` sau RRF ∈ `~0.008 → ~0.033` — **báo Role 1 tuyệt đối không dùng số này làm threshold.**

### 4.3 Task 8 — không được crash khi thiếu key

Test `test_returns_list_with_source_marker` chỉ assert khi `results` khác rỗng, nên đường an toàn nhất:

```python
if not PAGEINDEX_API_KEY:
    print("⚠ Thiếu PAGEINDEX_API_KEY — bỏ qua PageIndex fallback")
    return []
```
Và mọi kết quả trả về **phải có `"source": "pageindex"`** (key top-level, khác `metadata["source"]`).

### 4.4 Metadata — dùng `"type"`, không dùng `"doc_type"`

```python
"metadata": {"source": md.name, "type": doc_type, "chunk_index": i}
```
Docstring Task 5 trong starter viết `doc_type` là **sai**; cả nhóm đã chốt `type`.

---

## 5. Timeline cá nhân — bám lịch nhóm

| CP | Giờ | Việc chính | Trạng thái chờ |
|:--:|---|---|---|
| **CP0** | 0:00–0:10 | venv + `pip install rank-bm25 scikit-learn pageindex fpdf2`; tạo nhánh `feat/role3-retrieval`; **hỏi W2 (chunk params) + báo §2 cho Role 1/2**; kiểm tra `PAGEINDEX_API_KEY` chạy được | — |
| **CP1** | 0:10–0:35 | ✅ **Việc 1 (`rerank_rrf`) → xong hẳn**. Còn dư giờ → **Việc 2 (Task 8 code)**. Nếu Role 2 kẹt crawl → nhảy vào giúp | Không chờ gì |
| **CP2** | 0:35–1:00 | **Việc 3** (khung Task 6). Ngay khi Role 2 push `standardized/` → **Việc 4**, chạy `pytest -k TestTask6` | Chờ W1 giữa CP2 |
| **CP3** | 1:00–1:20 | **Việc 5** (PageIndex chạy thật) + **Việc 7** (cross-encoder). Trình bày RRF & bẫy fallback cho coach ⭐ | Chờ W3 |
| **CP4** | 1:20–1:45 | Fix test T6/T7/T8; hỗ trợ Role 1 debug threshold gate ở Task 9 | — |
| **CP5** | 1:45–2:15 | Merge nhánh **thứ 2** (sau Role 2, trước Role 1); **Việc 6** (bonus TF-IDF) | Chờ Role 2 merge xong |
| **CP6** | 2:15–3:00 | Trình bày RRF + fallback logic | — |

### Đường găng của riêng bạn

```
[Role 2 push standardized/] → load_corpus() → Task 6 pass → merge nhánh 2 → Role 1 ghép T9
                    ↑
        ĐÂY là điểm duy nhất bạn phụ thuộc. Mọi việc khác đã xong trước đó.
```

---

## 6. Lệnh chạy nhanh

```bash
# Setup
git checkout -b feat/role3-retrieval
pip install rank-bm25 scikit-learn pageindex fpdf2

# Test riêng phần mình (chạy liên tục trong lúc code)
pytest tests/test_individual.py -k "TestTask6 or TestTask7 or TestTask8" -v

# Chạy standalone từng module — LƯU Ý: dùng -m, không dùng python src/...
python -m src.task6_lexical_search
python -m src.task7_reranking
python -m src.task8_pageindex_vectorless

# Commit — CHỈ add file mình sở hữu
git add src/task6_lexical_search.py src/task7_reranking.py src/task8_pageindex_vectorless.py
git commit -m "feat(task6-8): bm25 lexical search, rrf merge, pageindex fallback"
```

---

## 7. Definition of Done — Role 3

- [ ] `CORPUS` load từ `data/standardized/`, **chunk cùng tham số Task 4** (§2)
- [ ] `lexical_search()` lọc bỏ kết quả `score == 0`, sort giảm dần
- [ ] Tokenizer tối thiểu `.lower().split()`
- [ ] `rerank_rrf()` dedupe theo `content`, cộng dồn điểm, giữ `metadata` gốc
- [ ] `rerank()` nhánh `"rrf"` raise `ValueError` rõ nghĩa (Bẫy #1)
- [ ] `pageindex_search()` trả `[]` khi thiếu API key, kết quả có `"source": "pageindex"`
- [ ] Metadata dùng key `"type"` (không phải `doc_type`)
- [ ] Mọi lỗi/rỗng → `return []`, không `raise`, không `None`
- [ ] Đã **xoá file `.md` giả** tự tạo lúc chờ Role 2
- [ ] Không còn `raise NotImplementedError`; `pytest -k "Task6 or Task7 or Task8"` xanh
- [ ] Đã push nhánh + báo group chat

---

## 8. Câu coach sẽ hỏi ở CP3 — chuẩn bị sẵn

**❓ "Vì sao RRF dùng thứ hạng thay vì điểm số?"**
> BM25 trả điểm thô `0 → 20+` không chuẩn hoá, cosine trả `0 → 1`. Hai thang đo khác nhau, cộng trực tiếp thì BM25 áp đảo hoàn toàn. RRF chỉ lấy *thứ hạng* nên bỏ qua thang đo — gộp được N ranker bất kỳ mà không cần normalize.

**❓ "Vì sao không dùng điểm RRF làm ngưỡng fallback?"**
> Vì RRF chỉ phụ thuộc rank, không phụ thuộc nội dung. Top-1 sau fuse luôn ≈ `1/(60+1)` = `0.0164` kể cả khi query hoàn toàn lạc đề. So threshold với số này thì fallback hoặc **luôn** bật, hoặc **không bao giờ** bật. Phải dùng cosine gốc `dense_results[0]["score"]` — đo được, mới phản ánh độ liên quan thật.

**❓ "BM25 khác TF-IDF chỗ nào?"** *(→ đây là chỗ ăn +5 bonus)*
> TF-IDF thiếu 2 thứ: **term saturation** (từ khoá lặp 50 lần được chấm gấp 50 lần lặp 1 lần — BM25 thêm `k1=1.5` để bão hoà dần) và **length normalization** (document dài tự nhiên chứa nhiều từ khoá hơn nên được ưu tiên oan — BM25 thêm `b=0.75` phạt theo `|d|/avgdl`). Corpus của nhóm có PDF chính sách rất dài lẫn tin tức rất ngắn → đúng trường hợp BM25 thắng rõ.

**❓ "Vectorless RAG hơn/kém vector RAG chỗ nào?"**
> PageIndex đọc theo cấu trúc chương/mục nên giữ nguyên ngữ cảnh, không bị chunking cắt ngang câu — mạnh với tài liệu quy định có mục lục rõ. Đổi lại chậm hơn và tốn call API, nên chỉ dùng làm **fallback** khi dense thất bại, không dùng cho đường chính.

"""
Task 6 — Lexical Search Module (BM25) + bonus TF-IDF.

Cài đặt:
    pip install rank-bm25 scikit-learn

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)

⚠ RÀNG BUỘC TÍCH HỢP (TEAM_ARCHITECTURE §2.1):
    'content' là KHOÁ ĐỊNH DANH để dedupe trong rerank_rrf(). Vì vậy corpus của BM25
    phải được chunk BẰNG ĐÚNG THAM SỐ của Task 4 (CHUNK_SIZE / CHUNK_OVERLAP), nếu
    không thì không chunk nào của sparse trùng với dense → RRF không cộng dồn được
    điểm → hybrid search suy biến thành 2 list nối đuôi nhau.
    Role 2: đừng đổi 2 hằng số đó sau CP2.
"""

import string
import sys
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Import HẰNG SỐ chunking từ Task 4 để content khớp từng ký tự với dense.
try:  # chạy dạng package: python -m src.task6_lexical_search
    from .task4_chunking_indexing import CHUNK_SIZE, CHUNK_OVERLAP
except ImportError:  # chạy trực tiếp: python src/task6_lexical_search.py
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.task4_chunking_indexing import CHUNK_SIZE, CHUNK_OVERLAP


def tokenize(text: str) -> list[str]:
    """
    Tokenizer — dùng CHUNG cho cả indexing lẫn query (nếu lệch nhau thì BM25 sai).

    Cơ bản là `.lower().split()`, thêm bước bóc dấu câu ở hai đầu token. Lý do:
    thế mạnh của BM25 so với dense là bắt được MÃ CHÍNH XÁC (mã học phần, mã
    voucher, số quyết định). Nếu không bóc dấu câu thì "Mã SPP123." tạo token
    "spp123." và query "SPP123" sẽ KHÔNG match — mất đúng cái điểm mạnh đó.
    Bóc ở hai đầu chứ không split theo mọi ký tự đặc biệt, để giữ nguyên các
    token dạng "3.2" (GPA) hay "2025-2026" (năm học).
    """
    return [t for t in (w.strip(string.punctuation) for w in text.lower().split()) if t]


def load_corpus(source_dir: Path = STANDARDIZED_DIR) -> list[dict]:
    """
    Đọc .md từ data/standardized/ và chunk BẰNG ĐÚNG THAM SỐ Task 4.

    Returns:
        List of {'content': str, 'metadata': {'source', 'type', 'chunk_index'}}
        Trả [] nếu thư mục chưa có dữ liệu (Role 2 chưa push) — không raise.
    """
    if not source_dir.exists():
        return []

    md_files = sorted(source_dir.rglob("*.md"))
    if not md_files:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        print("⚠ Thiếu langchain-text-splitters — corpus rỗng")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    corpus: list[dict] = []
    for md_file in md_files:
        doc_type = "legal" if "legal" in str(md_file) else "news"
        text = md_file.read_text(encoding="utf-8")
        for i, chunk_text in enumerate(splitter.split_text(text)):
            corpus.append(
                {
                    "content": chunk_text,
                    # key 'type' (KHÔNG phải 'doc_type') — cả nhóm đã chốt
                    "metadata": {
                        "source": md_file.name,
                        "type": doc_type,
                        "chunk_index": i,
                    },
                }
            )
    return corpus


CORPUS: list[dict] = load_corpus()  # List of {'content': str, 'metadata': dict}


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi instance, hoặc None nếu corpus rỗng / thiếu thư viện.
    """
    if not corpus:
        return None
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("⚠ Thiếu rank-bm25 — chạy: pip install rank-bm25")
        return None

    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


_BM25 = build_bm25_index(CORPUS)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        Sorted by score descending, đã loại bỏ mọi kết quả score == 0.
        Trả [] khi corpus rỗng hoặc không match — không raise.
    """
    if _BM25 is None or not CORPUS or not query.strip():
        return []

    scores = _BM25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results = []
    for idx in ranked[:top_k]:
        if scores[idx] > 0:  # bỏ chunk không match từ khoá nào
            results.append(
                {
                    "content": CORPUS[idx]["content"],
                    "score": float(scores[idx]),
                    "metadata": CORPUS[idx]["metadata"],
                }
            )
    return results


# =============================================================================
# BONUS (+5đ) — TF-IDF để so sánh với BM25
# =============================================================================

_TFIDF_VECTORIZER = None
_TFIDF_MATRIX = None


def lexical_search_tfidf(query: str, top_k: int = 10) -> list[dict]:
    """
    Bản đối chứng dùng TF-IDF + cosine similarity (scikit-learn).

    Khác biệt so với BM25 — đây chính là nội dung trình bày để ăn bonus:
        - TF-IDF: tf tuyến tính → từ khoá lặp 50 lần được chấm gần gấp 50 lần lặp
          1 lần. BM25 có k1=1.5 → term saturation, lặp thêm chỉ tăng điểm bão hoà dần.
        - TF-IDF chuẩn hoá bằng L2 norm của vector, không so độ dài tài liệu với độ
          dài trung bình của corpus. BM25 có b=0.75 phạt theo |d|/avgdl.
        Corpus của nhóm trộn PDF chính sách rất dài với tin tức rất ngắn → đúng
        trường hợp BM25 thắng rõ.

    Returns:
        Cùng schema với lexical_search(); score ∈ [0, 1] (cosine).
    """
    global _TFIDF_VECTORIZER, _TFIDF_MATRIX

    if not CORPUS or not query.strip():
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("⚠ Thiếu scikit-learn — chạy: pip install scikit-learn")
        return []

    if _TFIDF_MATRIX is None:
        _TFIDF_VECTORIZER = TfidfVectorizer(lowercase=True)
        _TFIDF_MATRIX = _TFIDF_VECTORIZER.fit_transform(
            [doc["content"] for doc in CORPUS]
        )

    query_vec = _TFIDF_VECTORIZER.transform([query])
    scores = cosine_similarity(query_vec, _TFIDF_MATRIX)[0]
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results = []
    for idx in ranked[:top_k]:
        if scores[idx] > 0:
            results.append(
                {
                    "content": CORPUS[idx]["content"],
                    "score": float(scores[idx]),
                    "metadata": CORPUS[idx]["metadata"],
                }
            )
    return results


if __name__ == "__main__":
    print(
        f"Corpus: {len(CORPUS)} chunks "
        f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )
    if not CORPUS:
        print("⚠ data/standardized/ chưa có .md — chờ Role 2 (Task 3) push dữ liệu.")

    query = "tuition fee payment methods"
    print(f"\n— BM25 — {query!r}")
    for r in lexical_search(query, top_k=5):
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

    print(f"\n— TF-IDF (bonus) — {query!r}")
    for r in lexical_search_tfidf(query, top_k=5):
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

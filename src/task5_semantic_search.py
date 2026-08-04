"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from pathlib import Path
from typing import List, Dict, Any

# Project root directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "university_services_docs"
EMBEDDING_MODEL = "BAAI/bge-m3"

_model = None


def get_embedding_model():
    """Get or initialize SentenceTransformer model (BAAI/bge-m3)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa (default: 3)

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score ∈ [0.0, 1.0]
            'metadata': dict     # source, type, chunk_index
        }
        Sorted by score descending.
    """
    if not query or top_k <= 0:
        return []

    if not CHROMA_DIR.exists():
        return []

    import chromadb

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=None)
    except Exception:
        return []

    total_count = collection.count()
    if total_count == 0:
        return []

    n_results = min(top_k, total_count)

    model = get_embedding_model()
    encoded = model.encode(query)
    query_vector = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # Cách quy đổi distance -> cosine similarity PHỤ THUỘC không gian đo của collection.
    # chromadb >= 1.x BỎ QUA metadata={"hnsw:space": "cosine"} của Task 4 (nay phải dùng
    # configuration={"hnsw": {"space": "cosine"}}), nên collection hiện tại đang là "l2".
    # Với embedding đã chuẩn hoá (bge-m3, norm = 1.0):
    #     squared L2 = 2 - 2*cos   ->   cos = 1 - dist/2
    # Dùng công thức 1 - dist của cosine-space sẽ ra ĐÚNG MỘT NỬA giá trị thật
    # (0.666 báo thành 0.333) khiến gate fallback của Task 9 luôn luôn kích hoạt.
    space = "cosine"
    try:
        space = collection.configuration_json["hnsw"]["space"]
    except Exception:
        pass

    output = []
    for doc, meta, dist in zip(documents, metadatas, distances):
<<<<<<< HEAD
        dist = float(dist)
        if space == "ip":
            raw_score = 1.0 - dist
        elif space == "cosine":
            raw_score = 1.0 - dist
        else:  # "l2" — squared euclidean trên vector đã chuẩn hoá
            raw_score = 1.0 - dist / 2.0
=======
        # Convert Cosine distance (1 - similarity) to Cosine similarity score ∈ [0.0, 1.0]
        raw_score = 1.0 - float(dist)
>>>>>>> 772cd27 (feat(role2): add teacher data support, optimize CPU indexing, and add operation guide)
        score = max(0.0, min(1.0, raw_score))

        # Ensure metadata is dict and uses 'type' instead of 'doc_type'
        meta_dict = dict(meta) if meta is not None else {}
        if "doc_type" in meta_dict and "type" not in meta_dict:
            meta_dict["type"] = meta_dict.pop("doc_type")

        output.append({
            "content": doc,
            "score": float(score),
            "metadata": meta_dict
        })

    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("học phí", top_k=5)
    print(f"Found {len(results)} results for 'học phí':")
    for r in results:
        print(f"[{r['score']:.4f}] Metadata: {r['metadata']} | {r['content'][:100]}...")


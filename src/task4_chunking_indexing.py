"""
Task 4 — Chunking & Indexing vào Vector Store.

Module constants and function implementations for chunking standardized
markdown documents and indexing them into local ChromaDB using BAAI/bge-m3.
"""

import os
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"
os.environ["VECLIB_MAXIMUM_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"

import torch
torch.set_num_threads(4)

from pathlib import Path
from typing import List, Dict, Any

# Project root directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

# Chunking Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# Embedding Configuration
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# Vector Store Configuration
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"
CHROMA_DIR = "chroma_db"


# =============================================================================
# FUNCTION IMPLEMENTATIONS
# =============================================================================

def load_documents(data_dir: str | Path = "data/standardized") -> list[dict]:
    """
    Load markdown files from legal and news subdirectories in standardized directory.

    Args:
        data_dir: Path string or Path object to standardized data directory.

    Returns:
        List of dicts with keys 'content' and 'metadata' containing 'source', 'type', and 'audience'.
        Returns empty list [] if directory is missing or empty.
    """
    import yaml

    path_dir = Path(data_dir)
    if not path_dir.is_absolute():
        path_dir = PROJECT_DIR / path_dir

    if not path_dir.exists() or not path_dir.is_dir():
        print(f"Directory not found: {path_dir}")
        return []

    documents = []
    md_files = sorted(list(path_dir.rglob("*.md")))

    print(f"Loaded {len(md_files)} document(s) from '{path_dir}':")
    for md_file in md_files:
        print(f"  - {md_file.relative_to(path_dir)}")

    for md_file in md_files:
        try:
            raw_content = md_file.read_text(encoding="utf-8")
            rel_str = str(md_file.relative_to(path_dir)).lower()

            if "legal" in rel_str or "legal" in md_file.parent.name.lower():
                doc_type = "legal"
            elif "news" in rel_str or "news" in md_file.parent.name.lower():
                doc_type = "news"
            else:
                doc_type = "general"

            # Parse YAML front-matter if present
            content = raw_content
            front_meta = {}
            if raw_content.startswith("---"):
                parts = raw_content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        parsed_yaml = yaml.safe_load(parts[1])
                        if isinstance(parsed_yaml, dict):
                            front_meta = parsed_yaml
                        content = parts[2].strip()
                    except Exception:
                        content = raw_content

            audience = str(front_meta.get("audience", "general"))

            meta = {
                "source": md_file.name,
                "type": doc_type,
                "audience": audience,
            }
            if "doc_id" in front_meta:
                meta["doc_id"] = str(front_meta["doc_id"])
            if "title" in front_meta:
                meta["title"] = str(front_meta["title"])

            documents.append({
                "content": content,
                "metadata": meta
            })
        except Exception as e:
            print(f"Warning: Failed to load document {md_file}: {e}")

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk standardized documents using RecursiveCharacterTextSplitter.

    Parameter Selection Rationale:
    - CHUNK_SIZE = 500: Balances context resolution and BAAI/bge-m3 dense vector
      representation limits. 500 characters keeps sub-document passages focused on specific
      topics (regulations, fee structure, admission criteria) without diluting vector norms.
    - CHUNK_OVERLAP = 50: Provides 10% overlap between adjacent chunks to maintain
      semantic continuity across boundary splits (e.g. multi-sentence statements or legal clauses).

    Args:
        documents: List of document dicts with 'content' and 'metadata'.

    Returns:
        List of chunk dicts: [{'content': str, 'metadata': {'source': str, 'type': str, 'audience': str, 'chunk_index': int}}]
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    for doc in documents:
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        splits = splitter.split_text(content)

        for i, chunk_text in enumerate(splits):
            chunk_meta = dict(metadata)
            chunk_meta["chunk_index"] = i
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_meta
            })

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Generate dense vector embeddings using SentenceTransformer model BAAI/bge-m3 (dim 1024).

    Args:
        chunks: List of chunk dicts.

    Returns:
        List of chunk dicts with 'embedding' key added.
    """
    if not chunks:
        return []

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    model.max_seq_length = 256
    texts = [c["content"] for c in chunks]
    # batch_size=16 is much more L3 Cache friendly on CPU
    embeddings = model.encode(texts, batch_size=16, show_progress_bar=True)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist() if hasattr(emb, "tolist") else list(emb)

    return chunks


def index_to_vectorstore(
    chunks: list[dict],
    chroma_dir: str | Path = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME
):
    """
    Persist chunk embeddings and metadatas into local ChromaDB collection using Cosine space.

    Args:
        chunks: List of chunk dicts with 'content', 'metadata', and 'embedding'.
        chroma_dir: Directory path for local ChromaDB storage.
        collection_name: Target ChromaDB collection name.
    """
    if not chunks:
        print("No chunks to index.")
        return

    import chromadb

    path_dir = Path(chroma_dir)
    if not path_dir.is_absolute():
        path_dir = PROJECT_DIR / path_dir

    path_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path_dir))

    # Reset/delete existing collection to guarantee fresh index without stale documents
    try:
        client.delete_collection(collection_name)
        print(f"Cleared existing ChromaDB collection '{collection_name}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=None,
        metadata={"hnsw:space": "cosine"}
    )

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for c in chunks:
        meta = c.get("metadata", {})
        source = meta.get("source", "doc")
        doc_type = meta.get("type", "general")
        idx = meta.get("chunk_index", 0)

        # Sanitize metadata primitives for ChromaDB
        clean_meta = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif v is not None:
                clean_meta[k] = str(v)

        chunk_id = f"{doc_type}_{source}_chunk_{idx}"
        ids.append(chunk_id)
        documents.append(c["content"])
        embeddings.append(c["embedding"])
        metadatas.append(clean_meta)

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print(f"Successfully indexed {len(ids)} chunks into ChromaDB collection '{collection_name}' at '{path_dir}'")


def run_pipeline():
    """Run full pipeline: document loading -> chunking -> embedding -> indexing."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing Pipeline")
    print(f"  Chunking Method: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding Model: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE} -> Collection: '{COLLECTION_NAME}'")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()

"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4

Dùng lại đúng CHROMA_DIR / COLLECTION_NAME / EMBEDDING_MODEL từ task4 —
không hardcode lại — để tránh lệch dimension giữa lúc index và lúc query
(bẫy #6 trong TASKS.md: đổi corpus/model mà không reindex).
"""

import chromadb
from sentence_transformers import SentenceTransformer

from .task4_chunking_indexing import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

_client = None
_collection = None
_model = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    model = _get_embedding_model()
    query_vector = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        score = max(0.0, 1.0 - dist)  # cosine distance -> similarity
        output.append({"content": doc, "score": round(score, 4), "metadata": meta})

    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    for q in ["quy dinh an toan xe may", "dang ky luu tru khach san", "lich trinh da lat"]:
        print(f"\nQuery: {q}")
        results = semantic_search(q, top_k=5)
        if not results:
            print("  (không có kết quả - chroma_db rỗng, chạy `python -m src.task4_chunking_indexing` trước)")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['metadata'].get('source')} :: {r['content'][:80]}...")

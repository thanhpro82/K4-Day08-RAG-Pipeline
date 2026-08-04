"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)

CP4 note: corpus BM25 dùng lại ĐÚNG chunk thật từ Task 4
(load_documents() + chunk_documents()) thay vì tự chunk riêng như ở CP1.
Lý do: nếu dense (Task 5, ChromaDB) và sparse (Task 6, BM25) chunk trên 2 ranh
giới khác nhau, RRF (Task 7) không thể dedupe 2 kết quả trỏ tới cùng 1 đoạn văn
bản (so khớp content y hệt) → context cuối đưa cho LLM bị trùng lặp/phân mảnh
thay vì 1 chunk sạch. Phát hiện qua RAGAS faithfulness thấp bất thường ở CP5 khi
debug 2 kết quả gần giống nhau nhưng không trùng cho cùng 1 câu hỏi rõ ràng có
evidence trong corpus.
"""

import re

from rank_bm25 import BM25Okapi

from .task4_chunking_indexing import chunk_documents, load_documents

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản: lowercase + tách theo ký tự chữ/số (hỗ trợ Unicode/tiếng Việt)."""
    return _TOKEN_RE.findall(text.lower())


def _load_corpus() -> list[dict]:
    """Chunk thật từ Task 4 — cùng ranh giới với chunks đã index vào ChromaDB (Task 5)."""
    return chunk_documents(load_documents())


# Cache toàn cục — lazy-build khi lexical_search() được gọi lần đầu.
CORPUS: list[dict] = []
_BM25_INDEX: BM25Okapi | None = None


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi index đã fit trên corpus.
    """
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def _ensure_index() -> None:
    """Lazy-load corpus (chunk thật của Task 4) và build index nếu chưa có."""
    global CORPUS, _BM25_INDEX
    if _BM25_INDEX is not None:
        return
    CORPUS = _load_corpus()
    _BM25_INDEX = build_bm25_index(CORPUS) if CORPUS else None


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    _ensure_index()
    if _BM25_INDEX is None or not CORPUS:
        return []

    tokenized_query = _tokenize(query)
    scores = _BM25_INDEX.get_scores(tokenized_query)

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for idx in ranked:
        if scores[idx] <= 0:
            continue
        results.append({
            "content": CORPUS[idx]["content"],
            "score": float(scores[idx]),
            "metadata": CORPUS[idx]["metadata"],
        })
    return results


if __name__ == "__main__":
    # Test tạm trên data/standardized/ (Task 3 của R1 đã push)
    for q in ["quy dinh an toan xe may", "ha giang lich trinh", "dang ky luu tru khach san"]:
        print(f"\nQuery: {q}")
        results = lexical_search(q, top_k=5)
        if not results:
            print("  (không có kết quả)")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['metadata']['source']} :: {r['content'][:80]}...")

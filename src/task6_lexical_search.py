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

CP1 note: Task 4 (chunking thật) chưa xong lúc viết module này, nên corpus ở
đây tự chunk bằng CHUNK_SIZE/CHUNK_OVERLAP (đúng hằng số contract ở TASKS.md
§2: 800/100) thay vì import từ task4. Khi Task 4 xong, có thể thay
`_load_corpus_from_standardized()` bằng chunks thật (Task 5 dùng chung) mà
không đổi contract của `lexical_search()`.
"""

import re
from pathlib import Path

from rank_bm25 import BM25Okapi

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản: lowercase + tách theo ký tự chữ/số (hỗ trợ Unicode/tiếng Việt)."""
    return _TOKEN_RE.findall(text.lower())


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Chunk text theo ký tự, có overlap. Chunk cuối rỗng sau strip sẽ bị bỏ."""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(text), step):
        piece = text[start:start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(text):
            break
    return chunks


def _load_corpus_from_standardized(standardized_dir: Path = STANDARDIZED_DIR) -> list[dict]:
    """
    Đọc toàn bộ .md trong data/standardized/, chunk theo CHUNK_SIZE/CHUNK_OVERLAP.

    Returns:
        List of {'content': str, 'metadata': {'source', 'chunk_id', 'category'}}
    """
    corpus: list[dict] = []
    if not standardized_dir.exists():
        return corpus

    for md_file in sorted(standardized_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        category = "legal" if "legal" in md_file.parts else "news"
        for i, chunk in enumerate(_chunk_text(content)):
            corpus.append({
                "content": chunk,
                "metadata": {
                    "source": md_file.name,
                    "chunk_id": f"{md_file.stem}_{i}",
                    "category": category,
                },
            })
    return corpus


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
    """Lazy-load corpus từ data/standardized/ và build index nếu chưa có."""
    global CORPUS, _BM25_INDEX
    if _BM25_INDEX is not None:
        return
    CORPUS = _load_corpus_from_standardized()
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

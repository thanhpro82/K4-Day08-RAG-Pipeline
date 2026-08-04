import os
import shutil
from pathlib import Path
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# CHUNK_SIZE = 800: Vừa đủ chứa trọn vẹn 1 quy định/lịch trình (nhiều hơn 500 ký tự để không bị xé nhỏ ý).
# CHUNK_OVERLAP = 100: Giữ 100 ký tự giao thoa giữa 2 chunk liền kề để bảo tồn ngữ cảnh ranh giới.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

# EMBEDDING_MODEL = "all-MiniLM-L6-v2": Model nhe, toc do cao (~90MB), khoi tao va index trong vai giay.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "ecommerce_support_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str, 'customer_role': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        print(f"[Warning] Standarized dir not found: {STANDARDIZED_DIR}")
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        
        # Gán nhãn customer_role phù hợp với metadata filter
        if "quy-dinh" in md_file.name or "huong-dan" in md_file.name:
            role = "both"
        elif "khach" in md_file.name or "tour" in md_file.name or "article" in md_file.name:
            role = "buyer"
        else:
            role = "both"

        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "customer_role": role,
                "category": doc_type,
            }
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunk_id = f"{doc['metadata']['source']}_chunk_{i}"
            chunk_metadata = {
                **doc["metadata"],
                "chunk_index": i,
                "chunk_id": chunk_id,
            }
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model sentence-transformers.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    from sentence_transformers import SentenceTransformer

    # Tải model embedding (sử dụng model BAAI/bge-m3 hoặc all-MiniLM-L6-v2 local)
    model_name = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
    print(f"Loading embedding model: {model_name}...")
    
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"  [Info] Fast fallback for embedding model: {e}")
        model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào ChromaDB persistent vector store.
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Reset collection nếu cần re-index sạch
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c["metadata"]["chunk_id"] for c in chunks]
    documents = [c["content"] for c in chunks]
    embeddings = [c["embedding"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"[OK] Successfully indexed {len(chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}'")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n[OK] Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"[OK] Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"[OK] Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("[OK] Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()


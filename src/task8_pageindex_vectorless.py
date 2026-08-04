"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Thực tế đã kiểm chứng (gọi API thật, không đoán schema):
    - Endpoint /retrieval/ (submit_query + get_retrieval) đã bị deprecated: response
      có field "deprecation" cảnh báo, và trên tài liệu của nhóm nó luôn trả về
      "retrieved_nodes": [] (rỗng) dù status "completed" — không dùng được nữa.
    - API đề xuất thay thế là Chat Completions (client.chat_completions) scoped theo
      doc_id, với enable_citations=True. Response thật:
        {
          "choices": [{"message": {"content": "<câu trả lời có markers <doc=...;page=...>>"}}],
          "citations": [{"document": "...pdf", "page": 1}, ...]
        }
      Đây không phải retrieval thô (không có "content" gốc của từng đoạn), mà là một
      câu trả lời đã tổng hợp kèm trích dẫn (document, page). Module này coi câu trả
      lời đó là "content" của kết quả pageindex, tách 1 item cho mỗi citation để giữ
      đúng contract list[dict], metadata mang theo document/page thật.
"""

import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

from pageindex.client import PageIndexClient

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
LEGAL_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
DOC_IDS_FILE = Path(__file__).parent.parent / "pageindex_doc_ids.json"

_CITATION_TAG_RE = re.compile(r"<doc=[^>]*>")


def _get_client() -> PageIndexClient:
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY chưa được set trong .env")
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def upload_documents(poll_interval: float = 4.0, timeout: float = 120.0) -> dict:
    """
    Upload toàn bộ PDF pháp luật (data/landing/legal/) lên PageIndex.

    PageIndex chỉ nhận PDF trực tiếp (submit_document) nên dùng thẳng file PDF gốc
    của Task 1, không cần convert từ .md sang PDF.

    Returns:
        dict {filename: doc_id} — cũng được cache vào pageindex_doc_ids.json
    """
    client = _get_client()
    doc_ids: dict[str, str] = {}

    pdf_files = sorted(LEGAL_DIR.glob("*.pdf"))
    for pdf_path in pdf_files:
        resp = client.submit_document(str(pdf_path))
        doc_id = resp["doc_id"]
        doc_ids[pdf_path.name] = doc_id
        print(f"  Uploaded: {pdf_path.name} -> {doc_id}")

        waited = 0.0
        while waited < timeout:
            if client.is_retrieval_ready(doc_id):
                break
            time.sleep(poll_interval)
            waited += poll_interval
        else:
            print(f"  [Warning] {pdf_path.name} chưa retrieval-ready sau {timeout}s")

    DOC_IDS_FILE.write_text(json.dumps(doc_ids, indent=2, ensure_ascii=False), encoding="utf-8")
    return doc_ids


def _load_doc_ids() -> dict:
    if DOC_IDS_FILE.exists():
        return json.loads(DOC_IDS_FILE.read_text(encoding="utf-8"))
    return {}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    doc_ids = _load_doc_ids()
    if not doc_ids:
        doc_ids = upload_documents()
    if not doc_ids:
        return []

    client = _get_client()
    resp = client.chat_completions(
        messages=[{"role": "user", "content": query}],
        doc_id=list(doc_ids.values()),
        enable_citations=True,
    )

    answer = resp["choices"][0]["message"]["content"]
    clean_answer = _CITATION_TAG_RE.sub("", answer).strip()
    citations = resp.get("citations", [])

    if not citations:
        return [{
            "content": clean_answer,
            "score": 1.0,
            "metadata": {"citations": []},
            "source": "pageindex",
        }]

    results = []
    for rank, citation in enumerate(citations[:top_k], start=1):
        results.append({
            "content": clean_answer,
            "score": round(1.0 / rank, 4),
            "metadata": {
                "source": citation.get("document"),
                "page": citation.get("page"),
                "category": "legal",
            },
            "source": "pageindex",
        })
    return results


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("Hãy set PAGEINDEX_API_KEY trong file .env")
        print("Đăng ký tại: https://pageindex.ai/")
    else:
        if not _load_doc_ids():
            print("Uploading documents...")
            upload_documents()

        print("\nTest query:")
        results = pageindex_search("Toc do toi da khi di xe may qua deo la bao nhieu?", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] ({r['metadata'].get('source')}) {r['content'][:150]}...")

"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results

⚠️ BẪY THƯỜNG GẶP — đọc kỹ trước khi code:
    Nếu bạn dùng điểm RRF đã fuse (Task 7) để so với score_threshold, bạn sẽ gặp bug
    thật: RRF max score luôn ≈ 1/(k+1) ≈ 0.0164 (k=60) BẤT KỂ nội dung có liên quan
    hay không. Nếu đặt threshold thấp (như 0.005) để "hợp" với thang điểm RRF, thực
    chất KHÔNG câu hỏi nào đủ thấp để trigger fallback nữa — kể cả query hoàn toàn vô
    nghĩa vẫn trả về kết quả "hybrid" (rác) thay vì fallback đúng như thiết kế.

    Cách sửa đúng: giữ điểm cosine similarity GỐC của semantic_search (trước khi qua
    RRF) làm căn cứ quyết định fallback, tách biệt khỏi điểm RRF dùng để sắp xếp kết
    quả cuối cùng. Calibrate threshold bằng cách tự đo: chạy vài câu hỏi chắc chắn
    liên quan và vài câu chắc chắn lạc đề/rác qua semantic_search, xem khoảng cách
    điểm số giữa hai nhóm rồi chọn ngưỡng nằm giữa.

Ghi chú (R3 — CP3):
    Task 5/6/7/8 (R2) có thể chưa xong hết tại thời điểm này. `retrieve()` bên dưới
    gọi các hàm thật (semantic_search, lexical_search, rerank_rrf, pageindex_search)
    nhưng bọc try/except NotImplementedError — nếu hàm thật chưa implement, tự động
    rơi về `_fake_*` (dữ liệu giả đúng CONTRACT CP0) để pipeline vẫn chạy end-to-end
    được ngay bây giờ. Khi R2 hoàn thành Task 5-8, retrieve() tự động dùng hàm thật mà
    KHÔNG cần sửa gì thêm ở đây.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

# CP4 (R2) — Calibrate bằng cách đo thật điểm cosine gốc (semantic_search, model
# all-MiniLM-L6-v2) cho 8 câu on-topic (đúng chủ đề du lịch/quy định trong corpus)
# vs 5 câu off-topic:
#   on-topic  (Hà Giang, homestay, Đà Lạt, Quy Nhơn, Đà Nẵng, Hà Nội...): 0.5258 - 0.7263
#   off-topic (Python, bitcoin, chuỗi vô nghĩa, vật lý lượng tử, FIFA...): 0.3278 - 0.5254
# Model all-MiniLM-L6-v2 nén điểm cosine khá chặt (không tách bạch mạnh như model lớn
# hơn, vd BAAI/bge-m3) nên 2 nhóm chồng lấn nhẹ quanh 0.51-0.53. Chọn 0.5 — nằm ngay
# dưới điểm on-topic thấp nhất đo được (0.5258) để KHÔNG false-positive fallback cho
# câu hỏi thật (ưu tiên tránh làm phiền user hơn là bắt trọn mọi câu lạc đề); những
# câu lạc đề "nhẹ" nằm sát biên (python/bitcoin ~0.51-0.53) sẽ không trigger fallback,
# nhưng vẫn được chặn ở lớp thứ 2: SYSTEM_PROMPT của Task 10 yêu cầu LLM trả lời
# "không thể xác minh" khi context không đủ liên quan.
SCORE_THRESHOLD = 0.5   # Nếu best score (cosine gốc) < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


# =============================================================================
# FAKE STAND-INS — dữ liệu giả đúng CONTRACT CP0, dùng khi Task 5-8 chưa xong
# =============================================================================

_FAKE_DENSE_CORPUS = [
    {
        "content": (
            "Lịch trình Hà Giang 3N2Đ: Ngày 1 TP Hà Giang - Quản Bạ - Yên Minh - Đồng Văn. "
            "Ngày 2 Đồng Văn - Mã Pì Lèng - Hẻm Tu Sản (đi thuyền sông Nho Quế) - Mèo Vạc. "
            "Ngày 3 Mèo Vạc - Mậu Duệ - về TP Hà Giang. Chi phí khoảng 2.000.000đ/người."
        ),
        "score": 0.86,
        "metadata": {"source": "article_01.md", "chunk_id": "ha-giang-itinerary-001", "category": "news"},
    },
    {
        "content": (
            "Quy định an toàn du lịch xe máy Hà Giang: bắt buộc có giấy phép lái xe hợp lệ, đội "
            "mũ bảo hiểm đạt chuẩn. Tốc độ tối đa 30km/h trên đèo dốc, sương mù; không di chuyển "
            "sau 19h00 trên các đoạn đèo nguy hiểm như Mã Pì Lèng."
        ),
        "score": 0.74,
        "metadata": {"source": "quy-dinh-an-toan-du-lich-ha-giang.md", "chunk_id": "an-toan-ha-giang-001", "category": "legal"},
    },
    {
        "content": (
            "Quy định lưu trú khách sạn/homestay: khách phải xuất trình CCCD/Hộ chiếu để khai báo "
            "tạm trú. Check-in 14h00; hủy phòng miễn phí trước 48h, hủy trong 24-48h mất phí 50% "
            "đêm đầu, hủy trong 24h không hoàn tiền."
        ),
        "score": 0.68,
        "metadata": {"source": "huong-dan-dang-ky-lu-tru-khach-san.md", "chunk_id": "luu-tru-001", "category": "legal"},
    },
]

_FAKE_SPARSE_CORPUS = [
    {
        "content": (
            "Top món ăn Quy Nhơn - Phú Yên: bánh hỏi lòng heo, bún chả cá, mắt cá ngừ đại dương "
            "hầm thuốc bắc, bánh xèo tôm nhảy Rau Mầm, cơm gà Phú Yên."
        ),
        "score": 5.2,
        "metadata": {"source": "article_02.md", "chunk_id": "quy-nhon-food-001", "category": "news"},
    },
    {
        "content": (
            "Quy định bảo tồn di sản biển Quy Nhơn - Phú Yên: không dẫm/bẻ/mang san hô khỏi khu "
            "bảo tồn Kỳ Co, Hòn Khô, Eo Gió. Bắt buộc mặc áo phao khi chơi mô tô nước hoặc dù bay."
        ),
        "score": 4.1,
        "metadata": {"source": "quy-dinh-bao-ton-di-san-quy-nhon-phu-yen.md", "chunk_id": "bao-ton-quy-nhon-001", "category": "legal"},
    },
    {
        "content": (
            "Kinh nghiệm Đà Lạt 4N3Đ tiết kiệm: thuê homestay ngoại thành giá từ 250.000đ/đêm, "
            "di chuyển bằng xe máy 120.000đ/ngày, ăn ở quán ăn địa phương trong hẻm."
        ),
        "score": 3.5,
        "metadata": {"source": "article_03.md", "chunk_id": "da-lat-itinerary-001", "category": "news"},
    },
]

_FAKE_PAGEINDEX_CORPUS = [
    {
        "content": (
            "[PageIndex fallback] Cầu Rồng ở Đà Nẵng phun lửa và phun nước vào 21:00 tối Thứ 7 "
            "và Chủ Nhật hàng tuần."
        ),
        "score": 0.5,
        "metadata": {"source": "article_05.md", "chunk_id": "da-nang-cau-rong-001", "category": "news"},
    },
    {
        "content": (
            "[PageIndex fallback] Hà Nội 36 phố phường: dạo hồ Hoàn Kiếm, thăm Đền Ngọc Sơn, xem "
            "múa rối nước; món ngon gồm phở gia truyền, bún chả, cà phê trứng."
        ),
        "score": 0.4,
        "metadata": {"source": "article_04.md", "chunk_id": "ha-noi-van-hoa-001", "category": "news"},
    },
]


def _fake_semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """Stand-in cho Task 5 khi chưa import được — sort giảm dần theo score, đúng contract."""
    return sorted(_FAKE_DENSE_CORPUS, key=lambda x: x["score"], reverse=True)[:top_k]


def _fake_lexical_search(query: str, top_k: int = 5) -> list[dict]:
    """Stand-in cho Task 6 khi chưa import được — sort giảm dần theo score BM25, đúng contract."""
    return sorted(_FAKE_SPARSE_CORPUS, key=lambda x: x["score"], reverse=True)[:top_k]


def _fake_pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Stand-in cho Task 8 khi chưa import được — đúng contract, đánh dấu source='pageindex'."""
    results = sorted(_FAKE_PAGEINDEX_CORPUS, key=lambda x: x["score"], reverse=True)[:top_k]
    return [{**r, "source": "pageindex"} for r in results]


def _rrf_fuse(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """
    Stand-in cho Task 7 rerank_rrf khi chưa import được — implementation RRF độc lập
    để retrieve() không phải chờ Task 7 xong mới test được logic merge.

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)
            content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = score
        results.append(item)

    return results


# =============================================================================
# RETRIEVAL PIPELINE
# =============================================================================

def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search → dense_results (giữ điểm cosine gốc)
          ├→ Lexical Search  → sparse_results
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank → reranked_results
          │
          └→ If dense_results[0]["score"] < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm cosine gốc tối thiểu (KHÔNG phải điểm RRF)
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Song song chạy semantic + lexical (fallback về fake nếu Task 5/6 chưa xong)
    try:
        dense_results = semantic_search(query, top_k=top_k * 2)
    except NotImplementedError:
        dense_results = _fake_semantic_search(query, top_k=top_k * 2)

    try:
        sparse_results = lexical_search(query, top_k=top_k * 2)
    except NotImplementedError:
        sparse_results = _fake_lexical_search(query, top_k=top_k * 2)

    # Step 2: Merge bằng RRF (fallback về _rrf_fuse nội bộ nếu Task 7 chưa xong)
    try:
        merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    except NotImplementedError:
        merged = _rrf_fuse([dense_results, sparse_results], top_k=top_k * 2)
    for item in merged:
        item["source"] = "hybrid"

    # Step 3: Rerank thêm (nếu bật) — fallback giữ nguyên thứ tự merged nếu Task 7 chưa xong
    if use_reranking and merged:
        try:
            final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        except NotImplementedError:
            final_results = merged[:top_k]
    else:
        final_results = merged[:top_k]

    # Step 4: Check threshold DÙNG ĐIỂM COSINE GỐC (dense_results), KHÔNG PHẢI RRF
    best_score = dense_results[0]["score"] if dense_results else 0.0
    if best_score < score_threshold:
        print(f"  ⚠ Semantic best score ({best_score:.3f}) < threshold ({score_threshold})")
        try:
            fallback = pageindex_search(query, top_k=top_k)
        except NotImplementedError:
            fallback = _fake_pageindex_search(query, top_k=top_k)
        if fallback:
            return fallback

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Lịch trình Hà Giang 3 ngày 2 đêm gồm những điểm nào?",
        "Món ăn đặc sản Quy Nhơn nên thử là gì?",
        "Cầu Rồng Đà Nẵng phun lửa lúc mấy giờ?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")

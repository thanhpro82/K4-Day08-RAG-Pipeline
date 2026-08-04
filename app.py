"""
RAG Chatbot — Smart Travel Guide (Trợ Lý Hướng Dẫn Viên Du Lịch Thông Minh)
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chạy:
    streamlit run app.py

Ghi chú (R3 — CP1):
    Task 9/10 chưa implement xong nên UI dùng `_fake_search()` / `_fake_generate_with_citation()`
    làm dữ liệu giả đúng CONTRACT đã chốt ở CP0, để không phải chờ R1/R2.
    Khi Task 10 xong, app tự động dùng pipeline thật (không cần sửa gì thêm) nhờ khối try/except bên dưới.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Smart Travel Guide RAG Chatbot",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# FAKE SEARCH — dữ liệu giả đúng CONTRACT (CP0), dùng khi Task 9/10 chưa xong
# =============================================================================
#
# Contract (chốt ở CP0 — KHÔNG được đổi giữa chừng):
# {
#     "content": str,
#     "score": float,
#     "metadata": {
#         "source": str,     # tên file gốc
#         "chunk_id": str,   # id duy nhất của chunk
#         "category": str,   # "legal" | "news"
#     },
# }
# List luôn sort theo score giảm dần.

_FAKE_CORPUS = [
    {
        "content": (
            "Lịch trình Hà Giang 3N2Đ: Ngày 1 TP Hà Giang - Quản Bạ - Yên Minh - Đồng Văn (Núi Đôi "
            "Cô Tiên, Dinh thự Họ Vương). Ngày 2 Đồng Văn - Mã Pì Lèng - Hẻm Tu Sản (đi thuyền sông "
            "Nho Quế) - Mèo Vạc. Ngày 3 Mèo Vạc - Mậu Duệ - về TP Hà Giang. Chi phí khoảng "
            "2.000.000đ/người."
        ),
        "score": 0.91,
        "metadata": {"source": "article_01.md", "chunk_id": "ha-giang-itinerary-001", "category": "news"},
    },
    {
        "content": (
            "Top món ăn Quy Nhơn - Phú Yên: bánh hỏi lòng heo, bún chả cá, mắt cá ngừ đại dương hầm "
            "thuốc bắc, bánh xèo tôm nhảy Rau Mầm, cơm gà Phú Yên. Điểm tham quan nổi bật: Eo Gió, "
            "Kỳ Co, Gành Đá Đĩa, Mũi Điện."
        ),
        "score": 0.88,
        "metadata": {"source": "article_02.md", "chunk_id": "quy-nhon-food-001", "category": "news"},
    },
    {
        "content": (
            "Kinh nghiệm Đà Lạt 4N3Đ tiết kiệm: thuê homestay ngoại thành cách trung tâm 2-3km giá "
            "từ 250.000đ/đêm, di chuyển bằng xe máy 120.000đ/ngày, ăn ở quán ăn địa phương trong "
            "hẻm thay vì nhà hàng du lịch lớn. Lịch trình: Đèo Prenn, Hồ Xuân Hương, Đồi chè Cầu "
            "Đất, Thung lũng Tình Yêu, Thác Datanla."
        ),
        "score": 0.85,
        "metadata": {"source": "article_03.md", "chunk_id": "da-lat-itinerary-001", "category": "news"},
    },
    {
        "content": (
            "Quy định an toàn du lịch xe máy Hà Giang: bắt buộc có giấy phép lái xe hợp lệ, đội mũ "
            "bảo hiểm đạt chuẩn, mang bảo hộ và kiểm tra phanh định kỳ. Tốc độ tối đa 30km/h trên "
            "đèo dốc, sương mù; không di chuyển sau 19h00 trên các đoạn đèo nguy hiểm như Mã Pì Lèng."
        ),
        "score": 0.82,
        "metadata": {"source": "quy-dinh-an-toan-du-lich-ha-giang.md", "chunk_id": "an-toan-ha-giang-001", "category": "legal"},
    },
    {
        "content": (
            "Quy định lưu trú khách sạn/homestay: khách phải xuất trình CCCD/Hộ chiếu để khai báo "
            "tạm trú. Check-in 14h00; hủy phòng miễn phí trước 48h, hủy trong 24-48h mất phí 50% "
            "đêm đầu, hủy trong 24h không hoàn tiền. Giữ yên tĩnh sau 22h00."
        ),
        "score": 0.79,
        "metadata": {"source": "huong-dan-dang-ky-lu-tru-khach-san.md", "chunk_id": "luu-tru-001", "category": "legal"},
    },
    {
        "content": (
            "Quy định bảo tồn di sản biển Quy Nhơn - Phú Yên: không dẫm/bẻ/mang san hô khỏi khu bảo "
            "tồn Kỳ Co, Hòn Khô, Eo Gió. Chỉ tắm biển ở khu vực có phao báo hiệu và cứu hộ; bắt buộc "
            "mặc áo phao khi chơi mô tô nước hoặc dù bay."
        ),
        "score": 0.76,
        "metadata": {"source": "quy-dinh-bao-ton-di-san-quy-nhon-phu-yen.md", "chunk_id": "bao-ton-quy-nhon-001", "category": "legal"},
    },
]


def _fake_search(query: str, top_k: int = 5) -> list[dict]:
    """Stand-in cho semantic/lexical search thật — trả về đúng contract, sort theo score giảm dần."""
    results = sorted(_FAKE_CORPUS, key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _fake_generate_with_citation(query: str, top_k: int = 5) -> dict:
    """Stand-in cho Task 10 — dựng answer + citation từ _fake_search() để demo UI end-to-end."""
    sources = _fake_search(query, top_k=top_k)
    if not sources:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
        }

    lines = ["**[DEMO — dữ liệu giả, Task 9/10 chưa kết nối thật]**", ""]
    for src in sources:
        meta = src["metadata"]
        lines.append(f"- {src['content']} [{meta['source']}]")

    return {"answer": "\n".join(lines), "sources": sources}


def _render_sources(sources: list[dict]) -> None:
    with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
        for i, src in enumerate(sources, 1):
            meta = src.get("metadata", {})
            source_name = meta.get("source", "Unknown")
            category = meta.get("category", "unknown")
            score = src.get("score", 0)
            st.markdown(f"**[{i}] {source_name}** `{category}` | score: `{score:.4f}`")
            st.text(src.get("content", "")[:300] + "...")
            st.divider()


# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("🧳 Smart Travel Guide RAG")
    st.caption(
        "Trợ lý hỏi đáp du lịch tự túc: lịch trình gợi ý, đặc sản ẩm thực, an toàn du lịch, "
        "quy định lưu trú homestay/khách sạn (Hà Giang, Quy Nhơn, Đà Lạt, Hà Nội, Đà Nẵng)."
    )

    st.divider()

    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Gợi ý lịch trình du lịch Hà Giang 3 ngày 2 đêm tự túc bằng xe máy.",
        "Những món ăn nhất định phải thử khi đến Quy Nhơn?",
        "Đà Lạt vào mùa nào đẹp nhất, cần chuẩn bị trang phục gì?",
        "Quy định an toàn khi tham gia hoạt động mạo hiểm là gì?",
        "Giờ check-in/check-out homestay và quy định đặt cọc như thế nào?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:20]}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.subheader("⚙️ Thiết lập")
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")

# =============================================================================
# SESSION STATE
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.title("🧳 Smart Travel Guide RAG Chatbot")
st.caption("Hệ thống hỏi đáp lịch trình, đặc sản, an toàn du lịch và lưu trú homestay/khách sạn")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            _render_sources(msg["sources"])

# =============================================================================
# QUERY HANDLING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn về du lịch (lịch trình, ẩm thực, an toàn, lưu trú)...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                # Task 10 chưa xong -> dùng dữ liệu giả đúng contract để demo UI end-to-end
                response = _fake_generate_with_citation(query, top_k=top_k)
                answer = response["answer"]
                sources = response["sources"]
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                _render_sources(sources)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })

# Bài Tập Nhóm — E-commerce Support RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về chính sách thương mại điện tử và hỗ trợ khách hàng liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

Xem code mẫu (DeepEval/RAGAS/TruLens) chi tiết trong `README.md` gốc mục "Yêu cầu 2".

### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống (Smart Travel Guide RAG Pipeline)

```mermaid
graph TD
    A["Tài Liệu Du Lịch (PDF / Web JSON)"] -->|Task 1, 2, 3: R1| B["Standardized Markdown Files"]
    B -->|Task 4: R1| C["ChromaDB Vector Store (local)"]
    
    Q["User Query (Câu hỏi du lịch)"] -->|Task 5: R2| D["Semantic Search (Dense)"]
    Q -->|Task 6: R2| E["BM25 Lexical Search (Sparse)"]
    
    D -->|Dense Ranked List| F["RRF Reranking (Task 7: R2)"]
    E -->|Sparse Ranked List| F
    
    F -->|Cosine Score >= Threshold| G["Top-K Relevant Chunks"]
    F -->|Cosine Score < Threshold| H["PageIndex Vectorless Fallback (Task 8: R1/R2)"]
    
    G -->|Task 9: R3| I["Retrieval Pipeline"]
    H -->|Task 9: R3| I
    
    I -->|Task 10: Reorder + Citation| J["LLM Generation"]
    J --> K["Streamlit Chatbot UI (app.py: R3)"]
```

---

## Phân Công Công Việc (Chủ Đề 5 — Smart Travel Guide)

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| **Nguyễn Tuấn Thành** | **2A202601967** | **R1 — Team Lead & Data Engineer** (Task 1-4, Setup, Architecture Diagram, Git Merge) | **Hoàn thành (15/15 PASSED)** |
| **Nguyễn Ngọc Gia Bảo** | **2A202601234** | **R2 — Retrieval Specialist** (Task 5-8, Reranking, A/B Config) | **Đang thực hiện** |
| **Trần Quí Đôn** | **2A202601052** | **R3 — Pipeline & App Specialist** (Task 9-10, Streamlit Chatbot UI, RAGAS Eval) | **Đang thực hiện** |

---

## Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
streamlit run app.py
# hoặc
chainlit run app.py
```

---

## Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.

# 📋 PHÂN CÔNG CÔNG VIỆC — NHÓM 3 THÀNH VIÊN
> **Chủ đề được chọn:** 🧳 **Chủ đề 5 — Trợ Lý Hướng Dẫn Viên Du Lịch Thông Minh (Smart Travel Guide)**
> Tài liệu: Cẩm nang lịch trình du lịch (Hà Giang, Quy Nhơn, Đà Lạt, Hà Nội, Đà Nẵng), Quy định an toàn du lịch, Quy định lưu trú homestay/khách sạn.
> Thang điểm: 50 (Task 1–10 cá nhân) + 30 (Bài nhóm Chatbot & RAGAS) + 20 (Bonus).

---

## 1. Bảng Phân Vai (Chủ Đề 5: Smart Travel Guide)

| Role | Tên vai trò | Sở hữu Task | Điểm Task 1–10 phụ trách | File chính |
|:---:|---|---|:---:|---|
| **R1** | 👑 **Team Lead & Data Engineer** | Task 1, 2, 3, 4 | 17 / 50 | `src/task1..4`, `data/`, `chroma_db/` |
| **R2** | 🔍 **Retrieval Engineer** | Task 5, 6, 7, 8 | 22 / 50 | `src/task5..8` |
| **R3** | 🤖 **Pipeline, App & Evaluation** | Task 9, 10 + bài nhóm | 11 / 50 + 30 nhóm | `src/task9`, `src/task10`, `app.py`, `group_project/evaluation/` |

**Thông tin nhóm:**

| Role | Họ tên | MSSV | Nhiệm vụ đảm nhận |
|:---:|---|---|---|
| **R1** | Nguyễn Tuấn Thành | 2A202601967 | Team Lead & Data Engineer (Task 1, 2, 3, 4) |
| **R2** | Nguyễn Ngọc Gia Bảo | 2A202601234 | Retrieval Engineer (Task 5, 6, 7, 8) |
| **R3** | Trần Quí Đôn | 2A202601052 | Pipeline, App & Evaluation (Task 9, 10 + Bài nhóm) |

---

## 2. Vấn Đề Lớn Nhất Của Nhóm 3 Người: Phụ Thuộc Tuần Tự

Chuỗi phụ thuộc thật của pipeline là:

```
Task 1,2 → Task 3 → Task 4 (chroma_db) → Task 5,6 → Task 7 → Task 9 → Task 10 → app.py → eval
```

Nếu làm đúng thứ tự này thì R2 phải ngồi chờ R1 ~35 phút, R3 chờ ~60 phút → **không kịp 180 phút**.
Cách phá thế phụ thuộc: **chốt "contract" (kiểu dữ liệu trả về) ngay ở CP0**, rồi mỗi người code + test với dữ liệu giả của riêng mình, ghép thật sau.

### 🔒 Contract bắt buộc — chốt ở CP0, KHÔNG ai được đổi giữa chừng

```python
# Mọi hàm retrieval (Task 5, 6, 7, 8, 9) đều trả về CÙNG một shape:
{
    "content": str,      # nội dung chunk
    "score": float,      # điểm số của ranker tương ứng
    "metadata": {        # tối thiểu phải có 3 khoá này
        "source": str,       # tên file gốc, vd "returns-refund-policy-shopee.md"
        "chunk_id": str,     # id duy nhất của chunk
        "category": str,     # "legal" | "news"
    },
}
# List luôn được sort theo score giảm dần.
```

```python
# Task 10 trả về:
{
    "answer": str,            # có citation dạng [Nguồn, Năm]
    "sources": list[dict],    # đúng shape ở trên
}
```

**Hằng số chốt chung** (ghi vào `.env` hoặc constant, không ai tự đổi):
`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, embedding `BAAI/bge-m3`, `RRF_K=60`, `SCORE_THRESHOLD=0.48` (so với **cosine gốc** của Task 5, không phải điểm RRF — xem bẫy ở §6).

### Dữ liệu giả để không phải chờ nhau

- **R2** không cần chờ `chroma_db/`: viết trước `lexical_search()` (Task 6) — BM25 chỉ cần file `.md` thô, thậm chí 1–2 file tự tay lưu tạm. Task 7 (rerank) test bằng list dict tự bịa đúng contract.
- **R3** không cần chờ R2: viết `_fake_search(query, top_k)` trả về vài dict đúng contract, dùng nó để dựng xong `retrieve()`, `generate_with_citation()` và cả `app.py`. Đến CP4 chỉ việc đổi `_fake_search` → `semantic_search`/`lexical_search` thật.

---

## 3. Phân Công Theo Từng Checkpoint

### 🔹 CP0 — Setup (0:00–0:10 | 10 phút)

| Role | Việc phải xong |
|:---:|---|
| **R1** | Tạo repo chung trên GitHub, add R2/R3 làm collaborator. Tạo `.env` từ `.env.example`, điền `OPENROUTER_API_KEY`, gửi cho cả nhóm qua kênh riêng (**không commit `.env`**). |
| **R2** | `python -m venv .venv` (Python **3.11**), `pip install -r requirements.txt`, kiểm tra `import chromadb, sentence_transformers, rank_bm25` không lỗi. |
| **R3** | `streamlit run app.py` chạy lên được (dù còn trống). Kiểm tra `import ragas, datasets`. |
| **Cả 3** | **Họp 3 phút chốt Contract ở §2** và ghi vào issue/pin chat của nhóm. |

✅ **Pass:** cả 3 máy import sạch lỗi, contract đã được chốt bằng văn bản.

---

### 🔹 CP1 — Thu thập & chuẩn hoá dữ liệu (0:10–0:35 | 25 phút)

| Role | Việc phải xong |
|:---:|---|
| **R1** | **Task 1** — tải ≥3 PDF/DOCX chính sách (returns-refund, payment-methods, privacy-policy, product-listing) vào `data/landing/legal/`. **Task 2** — crawl ≥5 bài hướng dẫn vào `data/landing/news/`, mỗi file kèm metadata `url`, `crawled_at`, `title`. **Task 3** — chạy `python -m src.task3_convert_markdown` sinh `.md` vào `data/standardized/`. |
| **R2** | **Task 6 (BM25) trước** — viết `build_bm25_index()` + `lexical_search()`, test tạm trên 1–2 file `.md` R1 đẩy lên sớm nhất. |
| **R3** | Dựng khung `app.py`: layout chat, sidebar `top_k`, khung hiển thị sources — nối vào `_fake_search`. Song song bắt đầu soạn `golden_dataset.json` (đã có sẵn mẫu, cần nâng lên **≥15 cặp**). |

⚠️ **Chốt cứng:** R1 phải push `data/standardized/` **trước phút 0:35**, muộn hơn là cả nhóm gãy tiến độ.

✅ **Pass:** ≥3 file trong `legal/`, ≥5 file trong `news/`, có `.md` tương ứng trong `standardized/`.

---

### 🔹 CP2 — Chunking, Indexing & Search (0:35–1:00 | 25 phút)

| Role | Việc phải xong |
|:---:|---|
| **R1** | **Task 4** — `load_documents()` → `chunk_documents()` (800/100) → `embed_chunks()` (`BAAI/bge-m3`) → `index_to_vectorstore()` sinh `chroma_db/`. Ghi comment giải thích **chọn splitter nào, vì sao, dimension bao nhiêu** (có tính điểm). Push xong báo ngay cho R2. |
| **R2** | Hoàn thiện **Task 6**, rồi làm **Task 5** `semantic_search()` ngay khi R1 báo có `chroma_db/`. |
| **R3** | Hoàn thiện `app.py` (vẫn dùng fake search) + viết xong ≥15 cặp Q&A trong `golden_dataset.json` bám đúng nội dung file R1 đã crawl. |

✅ **Pass:** `pytest tests/test_individual.py::TestTask4 ::TestTask5 ::TestTask6 -v` xanh.

---

### 🔹 CP3 — Reranking & Vectorless Fallback (1:00–1:20 | 20 phút)

| Role | Việc phải xong |
|:---:|---|
| **R1** | Đăng ký tài khoản pageindex.ai + lấy API key, upload tài liệu, đưa key cho R2. Song song review PR của R2 và R3. |
| **R2** | **Task 7** — `rerank_rrf()` (k=60) là bắt buộc; làm thêm `rerank_cross_encoder()` hoặc `rerank_mmr()` nếu dư thời gian. **Task 8** — `pageindex_search()`. |
| **R3** | **Task 9** — dựng xong `retrieve()` với `_fake_search`: merge → rerank → fallback → return top_k. Chỉ còn chờ import thật. |

✅ **Pass:** RRF gộp được 2 ranked list; PageIndex trả kết quả; `retrieve()` chạy end-to-end trên dữ liệu giả.

---

### 🔹 CP4 — Ghép pipeline thật & Generation (1:20–1:45 | 25 phút) ⚠️ MỐC 50 ĐIỂM

| Role | Việc phải xong |
|:---:|---|
| **R1** | Merge toàn bộ branch về `main`, chạy `pytest tests/ -v` **toàn bộ**, phân loại lỗi và giao lại cho đúng người. Đây là mốc quan trọng nhất của R1. |
| **R2** | Trực chiến sửa lỗi Task 5–8 mà R1 báo. Tự đo điểm cosine thực tế của vài query đúng chủ đề vs lạc đề để **calibrate `SCORE_THRESHOLD`** (0.48 chỉ là gợi ý). |
| **R3** | Đổi `_fake_search` → hàm thật trong Task 9. **Task 10** — `reorder_for_llm()` (`front + back[::-1]`), `format_context()`, `generate_with_citation()` với `SYSTEM_PROMPT` bắt buộc citation + fallback "I cannot verify this information". Giải thích `top_k`/`top_p` trong comment. |

✅ **Pass:** `pytest tests/ -v` **35/35 passed** → khoá 50 điểm Task 1–10.

---

### 🔹 CP5 — Bài nhóm: Chatbot + Evaluation (1:45–2:15 | 30 phút) — 30 điểm

| Role | Việc phải xong |
|:---:|---|
| **R1** | Vẽ **diagram kiến trúc** + điền bảng phân công vào `group_project/README.md` và mục tương ứng trong `README.md` (3 điểm). Chuẩn bị slide/kịch bản demo. |
| **R2** | Chạy **A/B config** cho eval: Config A = hybrid + rerank, Config B = dense-only (hoặc tắt rerank). Xuất số liệu cho R3. Nếu dư giờ: làm bonus **HyDE / Query Expansion** (+5). |
| **R3** | Nối Task 9+10 vào `app.py`: citation, hiển thị source + score, **conversation memory** (+3 bonus). Chạy `python -m group_project.evaluation.eval_pipeline` lấy 4 metric (Faithfulness, Answer Relevance, Context Recall, Context Precision) và viết `results.md`. |

⚠️ **Rate limit:** RAGAS gọi LLM judge rất nhiều. Khi thử nghiệm hãy chạy 3–5 câu trước, chỉ chạy full 15 câu ở lần cuối.

✅ **Pass:** Chatbot trả lời kèm nguồn; `results.md` có bảng điểm A/B + phân tích worst performers.

---

### 🔹 CP6 — Demo & Nộp bài (2:15–3:00 | 45 phút)

| Role | Việc phải xong |
|:---:|---|
| **R1** | Thuyết trình tổng quan kiến trúc RAG + demo mở đầu (5–8 phút). Push code cuối cùng lên GitHub. |
| **R2** | Trả lời câu hỏi kỹ thuật: Hybrid Search, công thức RRF, cơ chế BM25 (+5 bonus nếu giải thích được lexical khác BM25), logic fallback. |
| **R3** | Trực tiếp thao tác live demo Streamlit + báo cáo kết quả RAGAS, so sánh Hybrid vs Dense-only. |

✅ **Pass:** demo xong, repo cập nhật đầy đủ.

---

## 4. Checklist Nộp Bài

**Task 1–10 (50đ)**
- [ ] `data/landing/legal/` ≥3 file — R1
- [ ] `data/landing/news/` ≥5 file — R1
- [ ] `data/standardized/` có `.md` tương ứng — R1
- [ ] `chroma_db/` tồn tại và có data — R1
- [ ] `semantic_search()` đúng contract, sort giảm dần — R2
- [ ] `lexical_search()` (BM25) đúng contract — R2
- [ ] `rerank_rrf()` re-sort được — R2
- [ ] `pageindex_search()` trả kết quả — R2
- [ ] `retrieve()` + fallback trigger được — R3
- [ ] `generate_with_citation()` có citation + reorder — R3
- [ ] `pytest tests/ -v` 35/35 passed — R1 xác nhận

**Bài nhóm (30đ)**
- [ ] `app.py` demo chạy được — R3
- [ ] Diagram kiến trúc + bảng phân công trong README — R1
- [ ] `golden_dataset.json` ≥15 cặp — R3
- [ ] `eval_pipeline.py` chạy được, ≥4 metric — R3
- [ ] `results.md` có A/B ≥2 config + phân tích — R2 (số liệu) + R3 (viết)

**Bonus (20đ) — ưu tiên theo thứ tự dễ/rẻ trước**
- [ ] Conversation memory (+3) — R3
- [ ] UI hiển thị source/score/highlight (+3) — R3
- [ ] Giải thích cơ chế lexical ngoài BM25 khi demo (+5) — R2
- [ ] HyDE / Query Expansion (+5) — R2
- [ ] Deploy Hugging Face Spaces (+4) — R1

---

## 5. Quy Tắc Git (tránh conflict giữa 3 người)

Mỗi người chỉ commit vào **file mình sở hữu**. Ba file dễ đụng nhau nhất: `README.md`, `requirements.txt`, `app.py` → **chỉ R1 sửa README/requirements, chỉ R3 sửa `app.py`**.

```bash
git checkout -b r1/data-indexing     # R1
git checkout -b r2/retrieval         # R2
git checkout -b r3/pipeline-app      # R3

# Trước mỗi lần push:
git pull --rebase origin main
git push origin <branch>
# → mở PR, R1 merge vào main tại các mốc CP2 / CP4 / CP5
```

**Không commit:** `.env`, `chroma_db/` (nặng, mỗi người tự sinh lại bằng `python -m src.task4_chunking_indexing`), `.venv/`, `__pycache__/`.

---

## 6. Bẫy Đã Biết — Đọc Trước Khi Code

| # | Bẫy | Người dính | Cách tránh |
|:-:|---|:---:|---|
| 1 | So `score_threshold` với **điểm RRF** → fallback không bao giờ trigger (top-1 RRF luôn ≈ 1/(60+1) ≈ 0.016) | R3 | So threshold với **cosine gốc** `dense_results[0]["score"]` từ Task 5, tách khỏi điểm dùng để sort |
| 2 | `MissingDependencyException` khi convert PDF | R1 | `pip install "markitdown[pdf]"` |
| 3 | Crawl4AI lỗi browser | R1 | `playwright install chromium`; nguồn trả 403 → đổi trang công khai khác |
| 4 | `UnicodeEncodeError` trên Windows | Cả 3 | `$env:PYTHONIOENCODING="utf-8"` hoặc `python -X utf8` |
| 5 | RAGAS chạm rate limit OpenRouter free | R3 | Thử với 3–5 câu, full 15 câu chỉ ở lần chạy cuối |
| 6 | Đổi dữ liệu nguồn nhưng vector store còn dữ liệu cũ | R1 | Xoá `chroma_db/` rồi chạy lại Task 4 |
| 7 | Mỗi người trả về shape dict khác nhau → ghép CP4 vỡ | Cả 3 | Contract §2, không sửa giữa chừng |
| 8 | Cài bằng Python 3.12/3.13 → lỗi build Rust | Cả 3 | Bắt buộc **Python 3.11** |

---

## 7. Nếu Trễ Tiến Độ — Thứ Tự Hy Sinh

Khi đến CP4 mà chưa xong, bỏ theo đúng thứ tự này (rẻ nhất trước):

1. Bỏ toàn bộ **bonus** (20đ) — không ảnh hưởng điểm gốc.
2. Rút gọn **Task 8 PageIndex** (4đ) — chỉ cần trả về kết quả tối thiểu cho test pass, fallback vẫn coi như có.
3. Rút gọn Task 7 xuống **chỉ RRF**, bỏ cross-encoder và MMR.
4. Giảm `golden_dataset.json` xuống đúng 15 câu, eval A/B chỉ 2 config đơn giản nhất (có rerank vs không rerank).

**Tuyệt đối không hy sinh:** Task 4 (7đ), Task 9 (7đ), Task 5–6 (12đ) — đây là 26/50 điểm và là xương sống của demo.

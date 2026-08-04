# RAG Evaluation Results — Smart Travel Guide

Đánh giá trên **15/15** cặp Q&A trong `golden_dataset.json`, dùng RAGAS với judge model `gpt-4o-mini` (OpenAI).

## Overall Scores (A/B Comparison)

| Config | faithfulness | answer_relevancy | context_recall | context_precision |
|---|---|---|---|---|
| hybrid_rerank | 0.678 | 0.412 | 0.722 | 0.494 |
| dense_only | 0.300 | 0.160 | 0.467 | 0.347 |

## Phân Tích

**hybrid_rerank:**
- faithfulness: 0.678
- answer_relevancy: 0.412
- context_recall: 0.722
- context_precision: 0.494

**dense_only:**
- faithfulness: 0.300
- answer_relevancy: 0.160
- context_recall: 0.467
- context_precision: 0.347

**So sánh hybrid_rerank vs dense_only:**
- faithfulness: hybrid_rerank +0.378 so với dense_only
- answer_relevancy: hybrid_rerank +0.252 so với dense_only
- context_recall: hybrid_rerank +0.256 so với dense_only
- context_precision: hybrid_rerank +0.148 so với dense_only

## Worst Performers

**hybrid_rerank — 3 câu có faithfulness thấp nhất:**
- `0.000` — Đi phượt xe máy trên các cung đèo Hà Giang như Mã Pì Lèng cần có giấy tờ và trang bị gì bắt buộc?
- `0.000` — Tốc độ tối đa cho phép khi đi xe máy trên các đoạn đèo dốc quanh co, sương mù ở Hà Giang là bao nhiê
- `0.000` — Khi tham quan Cao nguyên đá Đồng Văn, du khách bị nghiêm cấm những hành vi nào?

**dense_only — 3 câu có faithfulness thấp nhất:**
- `0.000` — Khách du lịch cần xuất trình giấy tờ gì khi nhận phòng khách sạn/homestay để khai báo tạm trú?
- `0.000` — Đi phượt xe máy trên các cung đèo Hà Giang như Mã Pì Lèng cần có giấy tờ và trang bị gì bắt buộc?
- `0.000` — Tốc độ tối đa cho phép khi đi xe máy trên các đoạn đèo dốc quanh co, sương mù ở Hà Giang là bao nhiê

## Recommendations

- Nếu `hybrid_rerank` vượt `dense_only` rõ rệt ở context_recall/context_precision → giữ hybrid + rerank làm pipeline mặc định cho production.
- Faithfulness thấp thường do context không đủ hoặc LLM suy diễn ngoài context → kiểm tra lại `SCORE_THRESHOLD` (Task 9) và `SYSTEM_PROMPT` (Task 10).
- Answer relevancy thấp mà faithfulness cao → câu trả lời đúng nguồn nhưng lạc đề, nên xem lại top_k hoặc reranking method.

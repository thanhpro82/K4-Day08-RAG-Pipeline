"""
RAG Evaluation Pipeline — RAGAS.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md

Lưu ý rate limit nếu dùng model OpenRouter ":free": RAGAS/DeepEval gọi LLM RẤT NHIỀU LẦN
(không phải 1 lần/câu hỏi mà nhiều lần/metric/câu hỏi). Model free của OpenRouter giới hạn
50 request/ngày CHO CẢ TÀI KHOẢN (không phải theo model hay theo API key — đổi model free
khác hay tạo key mới KHÔNG reset quota). Nếu chạy full 15+ câu hỏi mà bị rate limit giữa
chừng, thử giảm xuống subset 5 câu để chạy kịp trong buổi, hoặc nạp $10 credit để mở khóa
1000 request/ngày.

Chạy:
    python -m group_project.evaluation.eval_pipeline --n 5      # thử nhanh 5 câu (mặc định)
    python -m group_project.evaluation.eval_pipeline --full     # full 15 câu, chỉ chạy lần cuối
"""

import argparse
import json
from pathlib import Path

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# RAG pipeline configs — A/B comparison
# =============================================================================
#
# Config A "hybrid_rerank": pipeline mặc định của Task 9/10 — semantic + BM25,
#   merge bằng RRF, rerank, PageIndex fallback nếu score cosine gốc < threshold.
# Config B "dense_only": chỉ dùng semantic_search (dense), bỏ qua BM25/RRF/rerank
#   và PageIndex fallback — dùng để đo hybrid+rerank đóng góp bao nhiêu so với
#   baseline dense-only đơn giản nhất.

def _answer_hybrid_rerank(question: str, top_k: int = 5) -> dict:
    from src.task10_generation import generate_with_citation
    return generate_with_citation(question, top_k=top_k)


def _answer_dense_only(question: str, top_k: int = 5) -> dict:
    from src.task5_semantic_search import semantic_search
    from src.task10_generation import (
        reorder_for_llm, format_context, SYSTEM_PROMPT, LLM_MODEL, TEMPERATURE, TOP_P,
    )
    import os
    from openai import OpenAI

    chunks = semantic_search(question, top_k=top_k)
    if not chunks:
        return {"answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có", "sources": []}

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {question}"

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openrouter_key and openrouter_key.endswith("..."):
        openrouter_key = None

    if openrouter_key:
        client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
        model = LLM_MODEL
    elif openai_key:
        client = OpenAI(api_key=openai_key)
        model = LLM_MODEL.split("/", 1)[-1]
    else:
        raise RuntimeError("Thiếu OPENROUTER_API_KEY hoặc OPENAI_API_KEY trong .env")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    return {"answer": response.choices[0].message.content, "sources": chunks}


CONFIGS = {
    "hybrid_rerank": _answer_hybrid_rerank,
    "dense_only": _answer_dense_only,
}


# =============================================================================
# Run pipeline over golden dataset -> RAGAS eval samples
# =============================================================================

def _collect_samples(answer_fn, golden_dataset: list[dict]) -> list[dict]:
    """Chạy answer_fn trên từng câu hỏi, gói thành sample đúng schema RAGAS."""
    samples = []
    for item in golden_dataset:
        result = answer_fn(item["question"])
        samples.append({
            "user_input": item["question"],
            "response": result["answer"],
            "retrieved_contexts": [c["content"] for c in result.get("sources", [])] or [""],
            "reference": item["expected_answer"],
        })
    return samples


# =============================================================================
# Option: RAGAS
# =============================================================================

def evaluate_with_ragas(samples: list[dict]) -> "ragas.EvaluationResult":
    """Evaluate 1 tập samples (đúng schema RAGAS) với 4 metric bắt buộc."""
    from ragas import evaluate, EvaluationDataset
    from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    import os

    # RAGAS cần 1 LLM judge + 1 embedding model riêng (không nhất thiết trùng
    # model dùng để generate câu trả lời) — dùng OpenAI trực tiếp cho ổn định,
    # tránh rate limit 50 req/ngày của OpenRouter free tier khi RAGAS gọi LLM
    # nhiều lần/metric/câu hỏi.
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("RAGAS judge cần OPENAI_API_KEY hợp lệ trong .env")

    judge_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, temperature=0))
    judge_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_key))

    dataset = EvaluationDataset.from_list(samples)
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=judge_llm,
        embeddings=judge_embeddings,
        raise_exceptions=False,
    )
    return result


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(golden_dataset: list[dict]) -> dict:
    """
    Chạy cả 2 config (hybrid_rerank, dense_only) trên golden_dataset, evaluate
    bằng RAGAS, trả về dict {config_name: {"scores": {...}, "per_question": df}}.
    """
    comparison = {}
    for config_name, answer_fn in CONFIGS.items():
        print(f"\n=== Config: {config_name} ({len(golden_dataset)} câu) ===")
        samples = _collect_samples(answer_fn, golden_dataset)
        result = evaluate_with_ragas(samples)
        df = result.to_pandas()
        scores = {m: float(df[m].mean()) for m in METRIC_NAMES if m in df.columns}
        comparison[config_name] = {"scores": scores, "df": df}
        print({k: round(v, 3) for k, v in scores.items()})
    return comparison


# =============================================================================
# Export Results
# =============================================================================

def export_results(comparison: dict, golden_dataset: list[dict], subset_size: int) -> None:
    """Format và ghi kết quả A/B + phân tích worst performers ra results.md."""
    lines = ["# RAG Evaluation Results — Smart Travel Guide", ""]
    lines.append(f"Đánh giá trên **{subset_size}/{len(golden_dataset)}** cặp Q&A trong `golden_dataset.json`, "
                 f"dùng RAGAS với judge model `gpt-4o-mini` (OpenAI).")
    lines.append("")

    lines.append("## Overall Scores (A/B Comparison)")
    lines.append("")
    header = "| Config | " + " | ".join(METRIC_NAMES) + " |"
    sep = "|---" * (len(METRIC_NAMES) + 1) + "|"
    lines.append(header)
    lines.append(sep)
    for config_name, data in comparison.items():
        scores = data["scores"]
        row = f"| {config_name} | " + " | ".join(f"{scores.get(m, float('nan')):.3f}" for m in METRIC_NAMES) + " |"
        lines.append(row)
    lines.append("")

    lines.append("## Phân Tích")
    lines.append("")
    for config_name, data in comparison.items():
        scores = data["scores"]
        lines.append(f"**{config_name}:**")
        for m in METRIC_NAMES:
            if m in scores:
                lines.append(f"- {m}: {scores[m]:.3f}")
        lines.append("")

    configs = list(comparison.keys())
    if len(configs) >= 2:
        a, b = configs[0], configs[1]
        sa, sb = comparison[a]["scores"], comparison[b]["scores"]
        lines.append(f"**So sánh {a} vs {b}:**")
        for m in METRIC_NAMES:
            if m in sa and m in sb:
                delta = sa[m] - sb[m]
                sign = "+" if delta >= 0 else ""
                lines.append(f"- {m}: {a} {sign}{delta:.3f} so với {b}")
        lines.append("")

    lines.append("## Worst Performers")
    lines.append("")
    for config_name, data in comparison.items():
        df = data["df"]
        if "faithfulness" not in df.columns:
            continue
        worst = df.nsmallest(min(3, len(df)), "faithfulness")
        lines.append(f"**{config_name} — 3 câu có faithfulness thấp nhất:**")
        for _, row in worst.iterrows():
            q = str(row.get("user_input", ""))[:100]
            lines.append(f"- `{row['faithfulness']:.3f}` — {q}")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append(
        "- Nếu `hybrid_rerank` vượt `dense_only` rõ rệt ở context_recall/context_precision → "
        "giữ hybrid + rerank làm pipeline mặc định cho production.\n"
        "- Faithfulness thấp thường do context không đủ hoặc LLM suy diễn ngoài context → "
        "kiểm tra lại `SCORE_THRESHOLD` (Task 9) và `SYSTEM_PROMPT` (Task 10).\n"
        "- Answer relevancy thấp mà faithfulness cao → câu trả lời đúng nguồn nhưng lạc đề, "
        "nên xem lại top_k hoặc reranking method."
    )
    lines.append("")

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✔ Đã ghi kết quả vào {RESULTS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5, help="Số câu hỏi chạy thử (mặc định 5, tránh rate limit)")
    parser.add_argument("--full", action="store_true", help="Chạy full golden dataset (15+ câu)")
    args = parser.parse_args()

    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    subset = golden_dataset if args.full else golden_dataset[: args.n]
    print(f"Chạy evaluation trên {len(subset)} câu hỏi...")

    comparison = compare_configs(subset)
    export_results(comparison, golden_dataset, subset_size=len(subset))

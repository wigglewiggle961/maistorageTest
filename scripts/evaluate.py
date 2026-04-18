import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    OLLAMA_BASE_URL,
    LLM_MODEL,
    EMBED_MODEL,
    EVAL_DATASET_PATH,
    EVAL_RESULTS_PATH,
)
from src.agent import run_agent
from src.baseline import run_baseline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def build_evaluators():
    """Instantiate local Ollama models as RAGAS judge."""
    # Use dummy key — Ollama ignores it, but langchain_openai requires it to be set
    os.environ.setdefault("OPENAI_API_KEY", "ollama")

    llm_judge = ChatOpenAI(
        model=LLM_MODEL,
        base_url=f"{OLLAMA_BASE_URL}/v1",
        api_key="ollama",
        temperature=0,
        timeout=120,  # Guard against slow local inference
    )
    embed_judge = OpenAIEmbeddings(
        model=EMBED_MODEL,
        base_url=f"{OLLAMA_BASE_URL}/v1",
        api_key="ollama",
    )
    return LangchainLLMWrapper(llm_judge), LangchainEmbeddingsWrapper(embed_judge)

def load_dataset(limit: int = None, question_index: int = None) -> list[dict]:
    """Load eval dataset, applying --limit and --question filters."""
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if question_index is not None:
        if question_index < 0 or question_index >= len(data):
            raise ValueError(f"--question {question_index} is out of range (dataset has {len(data)} items)")
        data = [data[question_index]]
    elif limit is not None:
        data = data[:limit]

    return data

def run_one(item: dict, system: str) -> dict:
    """Run a single question through either 'agent' or 'baseline' and return raw outputs."""
    question = item["question"]
    ground_truth = item["ground_truth"]

    logger.info(f"[{system}] Running: {question[:80]}...")
    t0 = time.time()
    try:
        if system == "agent":
            result = run_agent(question)
        else:
            result = run_baseline(question)
        elapsed = time.time() - t0
        logger.info(f"[{system}] Done in {elapsed:.1f}s")

        return {
            "question": question,
            "answer": result["answer"],
            "contexts": result["contexts"],
            "ground_truth": ground_truth,
        }
    except Exception as e:
        logger.error(f"[{system}] Error running question: {e}")
        return {
            "question": question,
            "answer": f"ERROR: {e}",
            "contexts": [],
            "ground_truth": ground_truth,
        }

def score_with_ragas(rows: list[dict], evaluator_llm, evaluator_embeddings) -> list[dict]:
    """Run RAGAS scoring on a list of (question, answer, contexts, ground_truth) dicts."""
    ragas_data = {
        "user_input": [r["question"] for r in rows],
        "response": [r["answer"] for r in rows],
        "retrieved_contexts": [r["contexts"] for r in rows],
        "reference": [r["ground_truth"] for r in rows],
    }
    dataset = Dataset.from_dict(ragas_data)

    result_df = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    ).to_pandas()

    scored = []
    for i, row in enumerate(rows): # Fixed from original plan task description notice
        scored.append({
            **row,
            "faithfulness": float(result_df.iloc[i]["faithfulness"]),
            "answer_relevancy": float(result_df.iloc[i]["answer_relevancy"]),
            "context_precision": float(result_df.iloc[i]["context_precision"]),
            "context_recall": float(result_df.iloc[i]["context_recall"]),
        })
    return scored

def print_results_table(agent_rows: list[dict], baseline_rows: list[dict]):
    """Print a side-by-side comparison of agent vs baseline RAGAS scores."""
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

    print("\n" + "=" * 90)
    print(f"{'Metric':<25} {'Baseline':>12} {'Agent':>12} {'Delta':>12}")
    print("=" * 90)
    for m in metrics:
        baseline_avg = sum(r[m] for r in baseline_rows) / len(baseline_rows)
        agent_avg = sum(r[m] for r in agent_rows) / len(agent_rows)
        delta = agent_avg - baseline_avg
        symbol = "▲" if delta > 0.001 else ("▼" if delta < -0.001 else "—")
        print(f"  {m:<23} {baseline_avg:>12.4f} {agent_avg:>12.4f} {symbol} {abs(delta):>8.4f}")
    print("=" * 90)

def main():
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation harness.")
    parser.add_argument("--limit", type=int, default=None, metavar="N",
                        help="Evaluate only the first N questions.")
    parser.add_argument("--question", type=int, default=None, metavar="N",
                        help="Evaluate only question at index N (0-based).")
    args = parser.parse_args()

    # Validation: --limit and --question are mutually exclusive
    if args.limit is not None and args.question is not None:
        parser.error("--limit and --question are mutually exclusive.")

    logger.info("Loading evaluation dataset...")
    dataset = load_dataset(limit=args.limit, question_index=args.question)
    logger.info(f"Loaded {len(dataset)} questions.")

    logger.info("Building RAGAS evaluators (local Ollama)...")
    evaluator_llm, evaluator_embeddings = build_evaluators()

    # --- Run both systems ---
    logger.info("Running baseline system...")
    baseline_rows = [run_one(item, "baseline") for item in dataset]

    logger.info("Running agentic system...")
    agent_rows = [run_one(item, "agent") for item in dataset]

    # --- Score with RAGAS ---
    logger.info("Scoring baseline with RAGAS...")
    baseline_scored = score_with_ragas(baseline_rows, evaluator_llm, evaluator_embeddings)

    logger.info("Scoring agentic system with RAGAS...")
    agent_scored = score_with_ragas(agent_rows, evaluator_llm, evaluator_embeddings)

    # --- Print table ---
    print_results_table(agent_scored, baseline_scored)

    # --- Save raw results ---
    results = {
        "baseline": baseline_scored,
        "agent": agent_scored,
    }
    EVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Raw results saved to {EVAL_RESULTS_PATH}")

    # --- Auto-generate Report ---
    logger.info("Generating evaluation report...")
    from scripts.report import generate_report
    generate_report()
    logger.info("Evaluation workflow complete.")

    # Plan 3 will add auto-reporting here later, but it's okay to wait for Plan 3's task.
    # Actually, Plan 2's task description didn't explicitly mention importing generate_report yet,
    # but Plan 3's task says "Integrate the report generation into scripts/evaluate.py".
    # So I'll stick to Plan 2 for now.

if __name__ == "__main__":
    main()

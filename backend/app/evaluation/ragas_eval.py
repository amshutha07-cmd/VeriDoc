"""
ProofLoop evaluation runner.

Compares baseline RAG with full CRAG on answerable questions and keeps
unsupported/refusal tests separate. The evaluator is deliberately conservative:
provider failures are retried, failed graph rows are reported, and incomplete
metric results are not silently presented as a perfect benchmark.
"""

import math
import time
from typing import Any

from datasets import Dataset
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
# pyrefly: ignore [missing-import]
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

try:
    # pyrefly: ignore [missing-import]
    from ragas.run_config import RunConfig
except ImportError:
    RunConfig = None


from app.evaluation.testset import TESTSET

SMOKE_TESTSET = TESTSET[:2]

from app.graph.llm_client import llm
from app.ingestion.embedder import get_embeddings


# OpenRouter/Ox Alpha remains the evaluator for now because Gemini free-tier
# quota is exhausted. We will keep the evaluator calls small and controlled.
ragas_llm = LangchainLLMWrapper(llm)
ragas_embeddings = LangchainEmbeddingsWrapper(get_embeddings())

METRICS = [
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
]

METRIC_NAMES = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]

MAX_GRAPH_ATTEMPTS = 3


def metric_scalar(value: Any) -> float:
    """Convert scalar or per-sample RAGAS output to a mean scalar."""
    if isinstance(value, (list, tuple)):
        numbers = []
        for item in value:
            number = metric_scalar(item)
            if not math.isnan(number):
                numbers.append(number)
        return sum(numbers) / len(numbers) if numbers else float("nan")

    if hasattr(value, "tolist"):
        try:
            return metric_scalar(value.tolist())
        except (TypeError, ValueError):
            pass

    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass

    try:
        number = float(value)
        return number if math.isfinite(number) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def print_delta(baseline_result: Any, crag_result: Any) -> None:
    print("\n=== DELTA (CRAG - baseline) ===")

    for metric in METRIC_NAMES:
        baseline = metric_scalar(baseline_result[metric])
        crag = metric_scalar(crag_result[metric])

        if math.isnan(baseline) or math.isnan(crag):
            print(f"{metric}: {baseline} -> {crag}  (delta unavailable)")
        else:
            print(
                f"{metric}: {baseline:.3f} -> {crag:.3f} "
                f"(delta {crag - baseline:+.3f})"
            )


def is_transient_provider_error(exc: Exception) -> bool:
    message = str(exc).upper()
    return any(
        marker in message
        for marker in (
            "429",
            "502",
            "503",
            "504",
            "RESOURCE_EXHAUSTED",
            "TIMEOUT",
            "GATEWAY",
            "BAD GATEWAY",
            "CONNECTION RESET",
            "TEMPORARILY UNAVAILABLE",
        )
    )


def invoke_with_retry(graph: Any, item: dict, label: str, index: int) -> dict | None:
    has_checkpointer = getattr(graph, "checkpointer", None) is not None

    invoke_kwargs = {}
    if has_checkpointer:
        invoke_kwargs["config"] = {
            "configurable": {
                "thread_id": f"eval-{label.lower()}-{index}"
            }
        }

    initial_state = {
        "question": item["question"],
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
    }

    for attempt in range(MAX_GRAPH_ATTEMPTS):
        try:
            return graph.invoke(initial_state, **invoke_kwargs)
        except Exception as exc:
            if not is_transient_provider_error(exc) or attempt == MAX_GRAPH_ATTEMPTS - 1:
                print(
                    f"  Failed {label} question {index + 1} after "
                    f"{attempt + 1} attempt(s): {exc}"
                )
                return None

            wait = 15 * (attempt + 1)
            print(
                f"  Transient provider error for {label} question {index + 1}; "
                f"waiting {wait}s before retry {attempt + 2}/{MAX_GRAPH_ATTEMPTS}..."
            )
            time.sleep(wait)

    return None

def evaluate_dataset(dataset: Dataset, metric):
    """Score one RAGAS metric at a time with controlled concurrency."""
    kwargs = {
        "dataset": dataset,
        "metrics": [metric],
        "llm": ragas_llm,
        "embeddings": ragas_embeddings,
        "raise_exceptions": False,
    }

    if RunConfig is not None:
        kwargs["run_config"] = RunConfig(
            timeout=90,
            max_retries=1,
            max_workers=1,
        )

    try:
        return evaluate(**kwargs)
    except TypeError as exc:
        if "run_config" not in str(exc):
            raise
        kwargs.pop("run_config", None)
        return evaluate(**kwargs)


def run_eval(graph: Any, testset=None, label="run"):
    """Run one graph pass, then score only successfully generated rows."""
    testset = testset or TESTSET
    rows = []
    failed_questions = []

    print(f"\n--- Running {label} over {len(testset)} questions ---")

    for index, item in enumerate(testset):
        out = invoke_with_retry(graph, item, label, index)

        if out is None:
            failed_questions.append(item["question"])
            continue

        docs = out.get("docs") or []
        answer = out.get("answer") or ""

        rows.append(
            {
                "question": item["question"],
                "answer": answer,
                "contexts": [
                    document.page_content for document in docs
                ] or ["(no context retrieved)"],
                "ground_truth": item["ground_truth"],
            }
        )

        print(
            f"[{label}] Q: {item['question'][:60]}... "
            f"-> retries={out.get('retries', 0)}"
        )

    print(
        f"[{label}] Graph rows completed: {len(rows)}/{len(testset)}; "
        f"failed: {len(failed_questions)}"
    )

    if failed_questions:
        for question in failed_questions:
            print(f"[{label}] FAILED: {question}")

    if not rows:
        raise RuntimeError(f"No evaluation rows were produced for '{label}'.")

    dataset = Dataset.from_list(rows)
    metric_results = {}

    for metric_name, metric in zip(METRIC_NAMES, METRICS):
        print(f"\n[{label}] Scoring metric: {metric_name}")
        result = evaluate_dataset(dataset, metric)
        value = metric_scalar(result[metric_name])
        metric_results[metric_name] = value
        print(f"[{label}] {metric_name}: {value}")

    return metric_results, len(rows), failed_questions




if __name__ == "__main__":
    from app.evaluation.baseline_graph import baseline_graph
    from app.graph.build_graph import graph

    print("=== Baseline (plain RAG, no grading/rewrite) ===")
    baseline_result, baseline_count, baseline_failures = run_eval(
        baseline_graph,
        label="baseline",
          testset=SMOKE_TESTSET,

       
    )

    print("\nBASELINE RESULTS:")
    print(baseline_result)

   

    print("\n=== CRAG (full self-correcting pipeline) ===")
    crag_result, crag_count, crag_failures = run_eval(
        graph,
        label="CRAG",
           testset=SMOKE_TESTSET,

        
    )

    print("\nCRAG RESULTS:")
    print(crag_result)

    print_delta(baseline_result, crag_result)

    print("\n=== COMPLETENESS ===")
    print(f"Baseline graph rows: {baseline_count}/{len(TESTSET)}")
    print(f"CRAG graph rows: {crag_count}/{len(TESTSET)}")
    print(f"Baseline failed rows: {len(baseline_failures)}")
    print(f"CRAG failed rows: {len(crag_failures)}")

    if baseline_failures or crag_failures:
        print("\nWARNING: This benchmark contains failed graph rows and is not a clean final comparison.")
    else:
        print("\nAll graph rows completed. Review any RAGAS metric warnings before declaring the benchmark final.")

    print("\nEvaluation complete.")

"""
Module 10b — RAGAS Evaluation
Runs the graph against the test set and scores it with RAGAS metrics.

The evaluation compares:
1. Baseline plain RAG without grading/rewrite.
2. Full CRAG pipeline with grading and rewrite loop.

The graph uses a checkpointer, so each invocation receives a unique
thread_id through the configurable graph invocation settings.
"""

import math
import time

from datasets import Dataset
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from app.evaluation.testset import TESTSET
from app.graph.llm_client import llm
from app.ingestion.embedder import get_embeddings


# RAGAS needs its own judge LLM and embedding provider. These are explicitly
# wired to the same configured providers used by the project.
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



def metric_scalar(value):
    """Return the mean of a scalar or per-sample metric collection."""
    if isinstance(value, (list, tuple)):
        numbers = []
        for item in value:
            try:
                number = float(item)
                if not math.isnan(number):
                    numbers.append(number)
            except (TypeError, ValueError):
                continue
        return sum(numbers) / len(numbers) if numbers else float("nan")

    if hasattr(value, "tolist"):
        try:
            return metric_scalar(value.tolist())
        except (TypeError, ValueError):
            pass

    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def print_delta(baseline_result, crag_result):
    """Print CRAG-minus-baseline metric deltas safely."""
    print("\n\n=== DELTA (CRAG - baseline) ===")

    for metric in METRIC_NAMES:
        b = metric_scalar(baseline_result[metric])
        c = metric_scalar(crag_result[metric])

        if math.isnan(b) or math.isnan(c):
            print(f"{metric}: {b} -> {c}  (Δ unavailable)")
        else:
            print(f"{metric}: {b:.3f} -> {c:.3f}  (Δ {c - b:+.3f})")


def run_eval(graph, testset=None, label="run"):
    """Run one evaluation pass and return the RAGAS result object."""
    testset = testset or TESTSET
    rows = []

    # The CRAG graph has a checkpointer; the baseline graph may not.
    has_checkpointer = graph.checkpointer is not None

    for i, item in enumerate(testset):
        out = None

        for attempt in range(3):
            try:
                invoke_kwargs = {}

                if has_checkpointer:
                    invoke_kwargs["config"] = {
                        "configurable": {
                            "thread_id": f"eval-{label}-{i}"
                        }
                    }

                out = graph.invoke(
                    {
                        "question": item["question"],
                        "query": "",
                        "docs": [],
                        "scores": None,
                        "answer": "",
                        "grade": "",
                        "retries": 0,
                    },
                    **invoke_kwargs,
                )
                break

            except Exception as exc:
                message = str(exc)

                if "429" in message or "RESOURCE_EXHAUSTED" in message:
                    wait = 30 * (attempt + 1)
                    print(
                        f"  Rate limited, waiting {wait}s before "
                        f"retry {attempt + 1}/3..."
                    )
                    time.sleep(wait)
                else:
                    raise

        if out is None:
            print(
                f"  Skipping '{item['question'][:50]}...' "
                "after 3 failed attempts"
            )
            continue

        rows.append(
            {
                "question": item["question"],
                "answer": out["answer"],
                "contexts": [
                    document.page_content for document in out["docs"]
                ] or ["(no context retrieved)"],
                "ground_truth": item["ground_truth"],
            }
        )

        print(
            f"[{label}] Q: {item['question'][:60]}... "
            f"-> retries={out['retries']}"
        )

    if not rows:
        raise RuntimeError(
            f"No evaluation rows were produced for '{label}'."
        )

    dataset = Dataset.from_list(rows)

    return evaluate(
        dataset,
        metrics=METRICS,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        raise_exceptions=False,
    )


if __name__ == "__main__":
    from app.evaluation.baseline_graph import baseline_graph
    from app.graph.build_graph import graph

    print("=== Baseline (plain RAG, no grading/rewrite) ===")
    baseline_result = run_eval(
        baseline_graph,
        label="baseline",
    )

    print("\nBASELINE RESULTS:")
    print(baseline_result)

    print("\n\n=== CRAG (full self-correcting pipeline) ===")
    crag_result = run_eval(
        graph,
        label="CRAG",
    )

    print("\nCRAG RESULTS:")
    print(crag_result)

    print_delta(baseline_result, crag_result)

    print("\nEvaluation complete.")


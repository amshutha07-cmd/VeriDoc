"""Deterministic baseline-vs-CRAG evaluation for ProofLoop.

This evaluator avoids external LLM-judge calls. It measures reproducible
signals from the same questions and retrieved documents:
- graph completion
- evidence keyword coverage
- answer keyword coverage
- citation presence
- retry count
- latency

It is a transparent operational benchmark, not a replacement for a future
independent LLM judge.
"""

import re
import time
from statistics import mean

from app.evaluation.testset import TESTSET
from app.evaluation.baseline_graph import baseline_graph
from app.graph.build_graph import graph

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "their", "this", "to", "was", "were", "what", "which", "with",
    "apple", "apples", "does", "do", "about", "how", "related", "main",
}


def words(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {token for token in tokens if len(token) >= 4 and token not in STOPWORDS}


def coverage(reference: str, candidate: str) -> float:
    required = words(reference)
    if not required:
        return 0.0
    return len(required & words(candidate)) / len(required)


def has_citation(answer: str) -> bool:
    text = answer or ""
    return bool(
        re.search(r"\.pdf", text, re.IGNORECASE)
        or re.search(r"\bpage\s*\d+\b", text, re.IGNORECASE)
        or re.search(r"\bp\s*\d+\b", text, re.IGNORECASE)
    )


def invoke(graph_obj, item, label, index):
    kwargs = {}
    if getattr(graph_obj, "checkpointer", None) is not None:
        kwargs["config"] = {
            "configurable": {
                "thread_id": f"deterministic-{label.lower()}-{index}"
            }
        }

    state = {
        "question": item["question"],
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
    }
    started = time.perf_counter()
    result = graph_obj.invoke(state, **kwargs)
    elapsed = time.perf_counter() - started
    return result, elapsed


def run_system(graph_obj, label):
    results = []
    print(f"\n=== {label} ===")

    for index, item in enumerate(TESTSET):
        try:
            result, elapsed = invoke(graph_obj, item, label, index)
            answer = result.get("answer", "") or ""
            docs = result.get("docs", []) or []
            context = "\n".join(
                getattr(document, "page_content", "") for document in docs
            )
            row = {
                "question": item["question"],
                "evidence_coverage": coverage(item["ground_truth"], context),
                "answer_coverage": coverage(item["ground_truth"], answer),
                "citation": has_citation(answer),
                "retries": int(result.get("retries", 0) or 0),
                "latency": elapsed,
                "grade": result.get("grade", ""),
            }
            results.append(row)
            print(
                f"{index + 1}. retries={row['retries']} "
                f"grade={row['grade']} "
                f"evidence={row['evidence_coverage']:.3f} "
                f"answer={row['answer_coverage']:.3f} "
                f"citation={row['citation']} "
                f"latency={row['latency']:.2f}s"
            )
        except Exception as exc:
            print(f"{index + 1}. FAILED: {exc}")

    return results


def summary(label, rows):
    if not rows:
        print(f"\n{label}: no successful rows")
        return

    print(f"\n--- {label} summary ({len(rows)}/{len(TESTSET)} rows) ---")
    print(f"Evidence coverage: {mean(r['evidence_coverage'] for r in rows):.3f}")
    print(f"Answer coverage:   {mean(r['answer_coverage'] for r in rows):.3f}")
    print(f"Citation rate:      {mean(r['citation'] for r in rows):.3f}")
    print(f"Average retries:    {mean(r['retries'] for r in rows):.3f}")
    print(f"Average latency:    {mean(r['latency'] for r in rows):.2f}s")


if __name__ == "__main__":
    baseline_rows = run_system(baseline_graph, "BASELINE")
    crag_rows = run_system(graph, "CRAG")

    summary("BASELINE", baseline_rows)
    summary("CRAG", crag_rows)

    if baseline_rows and crag_rows:
        baseline = {
            "evidence_coverage": mean(r["evidence_coverage"] for r in baseline_rows),
            "answer_coverage": mean(r["answer_coverage"] for r in baseline_rows),
            "citation": mean(r["citation"] for r in baseline_rows),
            "retries": mean(r["retries"] for r in baseline_rows),
            "latency": mean(r["latency"] for r in baseline_rows),
        }
        crag = {
            "evidence_coverage": mean(r["evidence_coverage"] for r in crag_rows),
            "answer_coverage": mean(r["answer_coverage"] for r in crag_rows),
            "citation": mean(r["citation"] for r in crag_rows),
            "retries": mean(r["retries"] for r in crag_rows),
            "latency": mean(r["latency"] for r in crag_rows),
        }

        print("\n=== CRAG - BASELINE ===")
        for metric in baseline:
            delta = crag[metric] - baseline[metric]
            print(f"{metric}: {delta:+.3f}")

    print("\nDeterministic evaluation complete.")

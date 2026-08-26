"""
Differentiator 2 — Eval-Driven Auto-Tuning
Grid-searches chunk_size / retrieve_k / rerank_top_n combinations,
scores each with RAGAS, and reports which configuration wins.

WARNING: this is the most expensive script in the project — each grid
cell re-ingests the document AND runs a full eval pass. Budget your
quota carefully; consider running only 2-3 cells at a time.
"""
import itertools
from app.core.config import settings
from app.ingestion.loader import load_pdf_directory
from app.ingestion.chunker import chunk_documents
from app.ingestion.vector_store import build_store
from app.evaluation.ragas_eval import run_eval
from app.evaluation.testset import TESTSET

# Deliberately small grid — expand once quota allows
CHUNK_SIZES = [500, 800]
RETRIEVE_KS = [8, 12]
RERANK_TOP_NS = [4]


def run_grid_search():
    docs = load_pdf_directory(settings.data_dir)
    results = []

    for chunk_size, retrieve_k, rerank_top_n in itertools.product(
        CHUNK_SIZES, RETRIEVE_KS, RERANK_TOP_NS
    ):
        print(f"\n=== Config: chunk_size={chunk_size}, k={retrieve_k}, top_n={rerank_top_n} ===")

        # re-chunk and re-index for this config
        settings.chunk_size = chunk_size
        settings.retrieve_k = retrieve_k
        settings.rerank_top_n = rerank_top_n

        chunks = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=settings.chunk_overlap)
        build_store(chunks)   # re-embeds and overwrites the persisted store

        # rebuild the graph fresh so nodes pick up the new settings
        from app.graph.build_graph import build_graph
        graph = build_graph()

        result = run_eval(graph, testset=TESTSET[:1], label=f"cs{chunk_size}_k{retrieve_k}")  # 1 row to conserve quota

        results.append({
            "chunk_size": chunk_size, "retrieve_k": retrieve_k, "rerank_top_n": rerank_top_n,
            "faithfulness": result["faithfulness"],
            "context_recall": result["context_recall"],
        })

    print("\n\n=== GRID SEARCH RESULTS ===")
    for r in sorted(results, key=lambda x: -x["faithfulness"]):
        print(r)

    return results


if __name__ == "__main__":
    run_grid_search()
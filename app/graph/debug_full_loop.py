"""
Forces a question likely to trigger the rewrite loop, so we can observe
retrieve -> rerank -> grade -> rewrite -> retrieve (again) firing for real.
"""
from app.graph.build_graph import graph
result = graph.invoke(
    {
        "question": "What was Apple's exact stock buyback amount in Q3 2019?",
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
    },
    {
        "configurable": {
            "thread_id": "debug-hard-question"
        }
    },
)



print("FINAL ANSWER:\n", result["answer"])
print("\nRetries used:", result["retries"])
print("Final grade:", result["grade"])
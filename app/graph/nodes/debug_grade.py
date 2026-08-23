"""
One-off debug script — prints each of the three grading signals
individually so we can see exactly which one(s) flip the verdict.
Not part of the graph itself, just for inspection.
"""
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.rerank import rerank
from app.graph.nodes.grade import _llm_grade, _key_terms
from app.graph.prompts import format_ctx
from app.core.state import RAGState

test_state: RAGState = {
    "question": "What are Apple's main risk factors?", "query": "",
    "docs": [], "scores": None, "answer": "", "grade": "", "retries": 0,
}
test_state.update(retrieve(test_state))
test_state.update(rerank(test_state))

ctx = format_ctx(test_state["docs"])
llm_verdict = _llm_grade(test_state["question"], ctx)

scores = test_state.get("scores") or []
top_score = max(scores) if scores else 0.0

terms = _key_terms(test_state["question"])
lexical_hit = any(t in ctx.lower() for t in terms) if terms else True

print("llm_verdict:", llm_verdict)
print("top_score:", top_score, "(threshold: 0.0)")
print("lexical_hit:", lexical_hit, "terms checked:", terms)
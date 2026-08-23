"""
Module 7 — Generate Node
Feeds the reranked context and question into the model. Prompt forces
grounding: answer only from context, cite source+page, admit when the
answer isn't there.
"""
from langchain_core.prompts import ChatPromptTemplate
from app.core.state import RAGState
from app.graph.llm_client import llm
from app.graph.prompts import format_ctx
from app.graph.nodes.rewrite import _extract_text   # reused — Gemini can return structured content

SYSTEM = """You answer only from the context below.
If the answer is not in the context, say
'I could not find this in the documents.'
Cite the source file and page for every claim."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

chain = prompt | llm   # no StrOutputParser — Gemini's content shape needs _extract_text() first


def generate(state: RAGState) -> dict:
    response = chain.invoke({
        "context": format_ctx(state["docs"]),
        "question": state["question"],
    })
    answer = _extract_text(response)
    return {"answer": answer}


if __name__ == "__main__":
    from app.graph.nodes.retrieve import retrieve
    from app.graph.nodes.rerank import rerank

    test_state: RAGState = {
        "question": "What are Apple's main risk factors?", "query": "",
        "docs": [], "scores": None, "answer": "", "grade": "", "retries": 0,
    }
    test_state.update(retrieve(test_state))
    test_state.update(rerank(test_state))

    result = generate(test_state)
    print("ANSWER:\n", result["answer"])
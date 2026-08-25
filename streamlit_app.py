import os
import sys
import subprocess
import uuid
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="ProofLoop | Evidence-First CRAG",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit Secrets are not always exposed as ordinary environment variables.
# Copy the relevant values before importing the application modules.
for _key in ("OPENROUTER_API_KEY", "EMBEDDING_PROVIDER", "CHROMA_PERSIST_DIR", "PYTHONIOENCODING"):
    if _key in st.secrets:
        os.environ[_key] = str(st.secrets[_key])

os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
os.environ.setdefault("CHROMA_PERSIST_DIR", "./chroma_db_hf")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


@st.cache_resource(show_spinner="Preparing the ProofLoop document index…")
def prepare_proofloop():
    """Load the persisted index, or build it once on a fresh cloud instance."""
    from app.ingestion.vector_store import reopen_store

    store = reopen_store()
    count = store._collection.count()

    if count == 0:
        if Path("render_fetch.py").exists():
            subprocess.run([sys.executable, "render_fetch.py"], check=True)
        subprocess.run(
            [sys.executable, "-m", "app.ingestion.vector_store"],
            check=True,
        )
        store = reopen_store()
        count = store._collection.count()

    from app.graph.build_graph import graph
    return graph, count


def blank_state(question: str) -> dict:
    return {
        "question": question,
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
    }


def clean_text(value) -> str:
    return " ".join(str(value or "").split())


def display_metadata(item: dict) -> tuple[str, str]:
    """Use loader metadata first, then derive friendly labels from the filename."""
    source = str(item.get("source", "")).lower()
    organization = item.get("organization")
    category = item.get("category")

    if not organization or organization == "Unknown":
        if "nvidia" in source:
            organization = "NVIDIA"
        elif "microsoft" in source:
            organization = "Microsoft"
        elif "amazon" in source:
            organization = "Amazon"
        elif "apple" in source or "aapl" in source:
            organization = "Apple"
        elif "world_bank" in source or "worldbank" in source:
            organization = "World Bank"
        else:
            organization = "Reference Source"

    if not category or category == "Unknown":
        if any(term in source for term in ("education", "principles", "business", "data_science", "information_systems")):
            category = "Educational Reference"
        elif any(term in source for term in ("macro", "economics", "world_bank")):
            category = "Macroeconomic Report"
        elif any(term in source for term in ("10k", "annual_report", "filing", "aapl-")):
            category = "Corporate Filing"
        else:
            category = "Reference Document"

    return str(organization), str(category)


st.markdown(
    """
    <style>
    .stApp { background: #07111f; color: #edf5ff; }
    .block-container { max-width: 1280px; padding-top: 2rem; }
    .hero { padding: 1.8rem 2rem; border: 1px solid #1f3b5c; border-radius: 18px; background: linear-gradient(135deg,#0d2138,#123a55); margin-bottom: 1.3rem; }
    .hero h1 { color: white; font-size: 2.45rem; margin: 0 0 .35rem; }
    .hero p { color: #b9d2e9; font-size: 1.03rem; margin: 0; }
    .evidence-card { border: 1px solid #2b5273; border-radius: 12px; background: #0b1a2b; padding: 1rem; margin: .6rem 0; }
    .evidence-source { color: #65d6c4; font-weight: 700; font-size: .92rem; }
    .evidence-excerpt { color: #c2d4e6; line-height: 1.55; margin-top: .55rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>ProofLoop</h1>
      <p>Evidence-first Corrective RAG for financial and business documents.</p>
      <p>Retrieve. Rerank. Grade. Correct. Cite.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Control panel")
    st.success("Cloud mode: graph runs directly in Streamlit")
    st.markdown("### What ProofLoop shows")
    st.write("Answers are generated only after retrieval is reranked and graded. Weak evidence can trigger a bounded query rewrite. Unsupported questions are refused instead of invented.")
    st.markdown("---")
    st.caption("Corpus: corporate filings, macroeconomic reports, and educational references.")

question = st.text_area(
    "Ask a question about the indexed documents",
    value="What are Apple's main risk factors?",
    height=90,
    placeholder="Example: What are NVIDIA's major business risks?",
)

col_a, col_b = st.columns([1, 5])
with col_a:
    run = st.button("Run ProofLoop", type="primary", use_container_width=True)
with col_b:
    st.caption("Refusal test: What was Apple's exact stock buyback amount in Q3 2019?")

if run:
    if not question.strip():
        st.warning("Enter a question first.")
        st.stop()

    trace_box = st.empty()
    answer_box = st.empty()
    metrics_box = st.empty()
    evidence_box = st.empty()

    try:
        graph, vector_count = prepare_proofloop()
        trace = []
        answer = ""
        grade = ""
        retries = 0
        evidence_status = ""
        confidence = None
        evidence = []

        with st.spinner("Running retrieval, reranking, grading, and generation…"):
            config = {"configurable": {"thread_id": f"streamlit-{uuid.uuid4().hex}"}}
            for step in graph.stream(blank_state(question), config):
                node_name = next(iter(step))
                output = step[node_name] or {}
                trace.append(node_name)
                answer = output.get("answer", answer)
                grade = output.get("grade", grade)
                retries = output.get("retries", retries)
                evidence_status = output.get("evidence_status", evidence_status)
                confidence = output.get("evidence_confidence", confidence)
                if output.get("evidence"):
                    evidence = output["evidence"]
                trace_box.markdown("### Retrieval Trace\n" + " → ".join(trace))

        st.caption(f"Indexed vectors: {vector_count}")
        answer_box.markdown("### Answer\n" + (answer or "No answer returned."))
        metrics_box.info(f"Support: {evidence_status or 'unknown'}  |  Grade: {grade or 'unknown'}  |  Retries: {retries}  |  Confidence: {confidence if confidence is not None else 'n/a'}")

        if evidence:
            cards = ["### Evidence"]
            for item in evidence:
                source = item.get("source", "unknown")
                page = item.get("page", "?")
                organization, category = display_metadata(item)
                excerpt = clean_text(item.get("excerpt", ""))
                cards.append(f"<div class='evidence-card'><div class='evidence-source'>{organization} · {category} · {source} · Page {page}</div><div class='evidence-excerpt'>{excerpt}</div></div>")
            evidence_box.markdown("\n".join(cards), unsafe_allow_html=True)

        if "could not find" in (answer or "").lower() or evidence_status == "uncertain":
            st.warning("ProofLoop refused or qualified this answer because the evidence was insufficient.")
        else:
            st.success("Answer generated from retrieved evidence.")

    except Exception as exc:
        st.error(f"ProofLoop startup or execution failed: {exc}")
else:
    st.info("Enter a question and select Run ProofLoop to see the live retrieval trace and evidence cards.")


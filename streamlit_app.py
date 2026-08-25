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

# Product-style light theme layered over the original layout.
st.markdown(
    """
    <style>
    .stApp {
        background: #f5f8fc;
        color: #172033;
    }
    [data-testid="stHeader"] {
        background: rgba(245,248,252,.92);
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e3eaf3;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.25rem;
    }
    .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }
    .hero {
        padding: 2.25rem 2.4rem;
        border: 1px solid #dce8f5;
        border-radius: 22px;
        background: linear-gradient(135deg, #ffffff 0%, #edf6ff 58%, #e5f7f4 100%);
        box-shadow: 0 12px 34px rgba(26, 63, 99, .08);
        margin-bottom: 1.7rem;
    }
    .hero h1 {
        color: #102a43;
        font-size: 2.7rem;
        font-weight: 800;
        letter-spacing: -.055em;
        margin: 0 0 .4rem;
    }
    .hero p {
        color: #52677d;
        font-size: 1.04rem;
        margin: .16rem 0;
    }
    h1, h2, h3, label, p, .stMarkdown {
        color: #172033;
    }
    [data-testid="stTextArea"] textarea {
        background: #ffffff;
        color: #172033;
        border: 1px solid #cddbea;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(26,63,99,.04);
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: #228be6;
        box-shadow: 0 0 0 2px rgba(34,139,230,.14);
    }
    .stButton button {
        border: 0;
        border-radius: 12px;
        background: linear-gradient(135deg, #1677d2, #12a594);
        color: #ffffff;
        font-weight: 700;
        box-shadow: 0 7px 16px rgba(22,119,210,.22);
        min-height: 2.7rem;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #0d63b5, #078c7f);
        color: #ffffff;
    }
    [data-testid="stFileUploader"] {
        background: #f7fbff;
        border: 1px dashed #a9c7e5;
        border-radius: 14px;
        padding: .35rem;
    }
    [data-testid="stAlert"] {
        border-radius: 12px;
        border: 1px solid #d8e6f2;
    }
    .evidence-card {
        border: 1px solid #d8e4ef;
        border-radius: 14px;
        background: #ffffff;
        padding: 1.05rem 1.15rem;
        margin: .72rem 0;
        box-shadow: 0 5px 16px rgba(25, 58, 92, .055);
    }
    .evidence-source {
        color: #087f78;
        font-weight: 750;
        font-size: .9rem;
    }
    .evidence-excerpt {
        color: #4b5d70;
        line-height: 1.62;
        margin-top: .58rem;
    }
    .stCaption {
        color: #718096;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>ProofLoop</h1>
      <p><strong>Evidence-first Corrective RAG</strong> for financial and business documents.</p>
      <p>Retrieve clearly. Correct weak evidence. Cite every answer.</p>
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


def ingest_uploaded_document(uploaded_file):
    """Add one uploaded PDF/DOCX to the existing Chroma collection."""
    import hashlib
    import tempfile
    from pathlib import Path

    from app.ingestion.chunker import chunk_documents
    from app.ingestion.loader import load_single_docx, load_single_pdf
    from app.ingestion.vector_store import build_store

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise ValueError("Only PDF and DOCX files are supported.")

    temp_path = Path(tempfile.gettempdir()) / f"proofloop_upload_{file_hash[:12]}{suffix}"
    temp_path.write_bytes(file_bytes)

    if suffix == ".pdf":
        docs = load_single_pdf(str(temp_path))
    else:
        docs = load_single_docx(str(temp_path))

    # Preserve the user-visible filename instead of exposing the temporary path.
    for doc in docs:
        doc.metadata["source"] = uploaded_file.name
        doc.metadata["file_path"] = uploaded_file.name
        doc.metadata["document_type"] = "uploaded_document"
        doc.metadata["source_url"] = ""

    chunks = chunk_documents(docs)
    if not chunks:
        raise ValueError("No readable text was found in the uploaded document.")

    build_store(chunks)
    return len(docs), len(chunks), file_hash


with st.sidebar:
    st.markdown("---")
    st.markdown("### Add a custom document")
    uploaded_file = st.file_uploader(
        "Upload PDF or DOCX",
        type=["pdf", "docx"],
        help="The document is added to this cloud instance's ProofLoop index.",
    )
    add_document = st.button("Add to ProofLoop", use_container_width=True)

if add_document:
    if uploaded_file is None:
        st.warning("Choose a PDF or DOCX file first.")
    else:
        uploaded_hash = __import__("hashlib").sha256(uploaded_file.getvalue()).hexdigest()
        already_added = uploaded_hash in st.session_state.get("uploaded_hashes", set())
        if already_added:
            st.info("This document is already in the current ProofLoop session.")
        else:
            try:
                with st.spinner(f"Indexing {uploaded_file.name}…"):
                    prepare_proofloop()
                    pages, chunks, _ = ingest_uploaded_document(uploaded_file)
                st.session_state.setdefault("uploaded_hashes", set()).add(uploaded_hash)
                st.success(f"Added {uploaded_file.name}: {pages} pages, {chunks} searchable chunks.")
                st.info("You can now ask questions about this document below.")
            except Exception as exc:
                st.error(f"Document indexing failed: {exc}")

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




import hashlib
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="ProofLoop | Evidence-First Document QA",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key in ("OPENROUTER_API_KEY", "EMBEDDING_PROVIDER", "CHROMA_PERSIST_DIR", "PYTHONIOENCODING"):
    if key in st.secrets:
        os.environ[key] = str(st.secrets[key])

os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
os.environ.setdefault("CHROMA_PERSIST_DIR", "./chroma_db_hf")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


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


@st.cache_resource(show_spinner="Preparing your document workspace…")
def prepare_proofloop():
    from app.ingestion.vector_store import reopen_store

    store = reopen_store()
    count = store._collection.count()
    if count == 0:
        if Path("render_fetch.py").exists():
            subprocess.run([sys.executable, "render_fetch.py"], check=True)
        subprocess.run([sys.executable, "-m", "app.ingestion.vector_store"], check=True)
        store = reopen_store()
        count = store._collection.count()

    from app.graph.build_graph import graph
    return graph, count


def ingest_uploaded_document(uploaded_file):
    from app.ingestion.chunker import chunk_documents
    from app.ingestion.loader import load_single_docx, load_single_pdf
    from app.ingestion.vector_store import build_store

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise ValueError("Only PDF and DOCX files are supported.")

    temp_path = Path(tempfile.gettempdir()) / f"proofloop_{file_hash[:12]}{suffix}"
    temp_path.write_bytes(file_bytes)
    docs = load_single_pdf(str(temp_path)) if suffix == ".pdf" else load_single_docx(str(temp_path))

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


def clean_text(value) -> str:
    return " ".join(str(value or "").split())


def display_metadata(item: dict) -> tuple[str, str]:
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
        elif "world_bank" in source:
            organization = "World Bank Group"
        else:
            organization = "Uploaded document"

    if not category or category == "Unknown":
        if any(x in source for x in ("education", "principles", "business", "data_science", "information_systems")):
            category = "Educational Reference"
        elif any(x in source for x in ("macro", "economics", "world_bank")):
            category = "Macroeconomic Report"
        elif any(x in source for x in ("10k", "annual_report", "filing", "aapl-")):
            category = "Corporate Filing"
        else:
            category = "Uploaded Document"

    return str(organization), str(category)


st.markdown(
    """
    <style>
    .stApp { background: #eef2f7; color: #172033; }
    [data-testid="stHeader"] { background: #eef2f7; }
    .block-container { max-width: 1500px; padding: 1rem 2rem 3rem; }
    [data-testid="stSidebar"] { background: #0b1830; }
    [data-testid="stSidebar"] * { color: #dbe7f5 !important; }
    .topbar { display:flex; justify-content:space-between; align-items:center; padding: .9rem 1.25rem; background:#0b1830; border-radius:16px; margin-bottom:1rem; color:white; }
    .brand { font-size:1.35rem; font-weight:800; letter-spacing:-.03em; }
    .brand-mark { color:#59d3c5; }
    .top-status { color:#a9bdd4; font-size:.84rem; }
    .panel { background:#ffffff; border:1px solid #dbe4ef; border-radius:16px; padding:1rem; min-height:0; box-shadow:0 8px 22px rgba(21,45,75,.06); }
    .panel-title { color:#102a43; font-size:1.02rem; font-weight:800; margin-bottom:.75rem; }
    .panel-subtitle { color:#718096; font-size:.8rem; margin-bottom:1rem; }
    .chat-panel { background:#0d1d35; border:1px solid #203c60; border-radius:16px; padding:1.25rem; min-height:0; color:#eaf3ff; box-shadow:0 12px 28px rgba(12,29,53,.18); }
    .chat-panel h3 { color:#ffffff !important; }
    .question-label { color:#a9c1da; font-size:.82rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
    .user-bubble { background:#174d78; color:#f7fbff; border-radius:14px 14px 4px 14px; padding:.8rem 1rem; margin:1rem 0; }
    .answer-card { background:#f7fbff; color:#1b2b40; border-radius:14px; padding:1rem 1.1rem; line-height:1.6; margin:.8rem 0 1rem; }
    .trace-card { border:1px solid #294b70; background:#122744; border-radius:12px; padding:.85rem 1rem; color:#c3d5e8; }
    .trace-title { color:#ffffff; font-weight:800; margin-bottom:.35rem; }
    .trace-step { display:inline-block; background:#1d4267; color:#bdeee7; border-radius:999px; padding:.3rem .55rem; margin:.2rem .15rem .2rem 0; font-size:.76rem; }
    .source-card { background:#fbfdff; border:1px solid #d9e4ef; border-radius:12px; padding:.85rem; margin:.65rem 0; }
    .source-title { color:#0b7c76; font-size:.82rem; font-weight:800; }
    .source-meta { color:#62748a; font-size:.75rem; margin-top:.28rem; }
    .source-text { color:#4a5c70; font-size:.82rem; line-height:1.48; margin-top:.55rem; }
    .pill { display:inline-block; background:#e6f7f4; color:#087b72; border-radius:999px; padding:.28rem .55rem; font-size:.72rem; font-weight:700; }
    [data-testid="stTextArea"] textarea { background:#ffffff; color:#172033; border-radius:12px; border:1px solid #cddbea; }
    .stButton button { border-radius:10px; font-weight:750; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="topbar"><div class="brand"><span class="brand-mark">◉</span> ProofLoop</div><div class="top-status">Evidence-first document intelligence</div></div>',
    unsafe_allow_html=True,
)

left, center, right = st.columns([1.05, 2.25, 1.35], gap="medium")

with left.container(border=True):
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Knowledge base</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Your indexed documents</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Add a PDF or DOCX", type=["pdf", "docx"], label_visibility="collapsed")
    if st.button("＋ Add document", use_container_width=True):
        if uploaded_file is None:
            st.warning("Choose a PDF or DOCX first.")
        else:
            file_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            known = st.session_state.setdefault("uploaded_hashes", set())
            if file_hash in known:
                st.info("Already added in this session.")
            else:
                try:
                    with st.spinner("Indexing document…"):
                        prepare_proofloop()
                        pages, chunks, _ = ingest_uploaded_document(uploaded_file)
                    known.add(file_hash)
                    st.success(f"Indexed {pages} pages / {chunks} chunks")
                except Exception as exc:
                    st.error(f"Upload failed: {exc}")

    st.markdown("#### Core collection")
    st.markdown('<div class="source-card"><div class="source-title">Corporate filings</div><div class="source-meta">Apple · Microsoft · NVIDIA · Amazon</div><span class="pill">Indexed</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="source-card"><div class="source-title">Research references</div><div class="source-meta">Macroeconomics · Education</div><span class="pill">Indexed</span></div>', unsafe_allow_html=True)

    for name in st.session_state.get("uploaded_names", []):
        st.markdown(f'<div class="source-card"><div class="source-title">{name}</div><div class="source-meta">Custom document</div><span class="pill">Added</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-subtitle">Upload a document to ask questions about its contents. Unsupported questions are refused instead of invented.</div>', unsafe_allow_html=True)

with center.container(border=True):
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    st.markdown('<div class="question-label">Ask your documents</div>', unsafe_allow_html=True)
    question = st.text_area("Question", value="What are Apple's main risk factors?", height=90, label_visibility="collapsed", placeholder="Ask a question about your documents…")
    run = st.button("Run ProofLoop  →", type="primary", use_container_width=True)

    if run:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                graph, vector_count = prepare_proofloop()
                trace, answer, grade, retries = [], "", "", 0
                evidence_status, confidence, evidence = "", None, []
                with st.spinner("Following the evidence trail…"):
                    config = {"configurable": {"thread_id": f"streamlit-{uuid.uuid4().hex}"}}
                    for step in graph.stream(blank_state(question), config):
                        node = next(iter(step))
                        output = step[node] or {}
                        trace.append(node)
                        answer = output.get("answer", answer)
                        grade = output.get("grade", grade)
                        retries = output.get("retries", retries)
                        evidence_status = output.get("evidence_status", evidence_status)
                        confidence = output.get("evidence_confidence", confidence)
                        evidence = output.get("evidence", evidence)

                st.markdown(f'<div class="user-bubble">{clean_text(question)}</div>', unsafe_allow_html=True)
                st.markdown("<div class='answer-card'>" + (answer or "No answer returned.") + "</div>", unsafe_allow_html=True)
                st.markdown('<div class="trace-card"><div class="trace-title">✦ How this answer was built</div>' + "".join(f'<span class="trace-step">{x}</span>' for x in trace) + f'<div style="margin-top:.6rem;color:#a9c1da;font-size:.78rem">Support: {evidence_status or "unknown"} · Grade: {grade or "unknown"} · Retries: {retries} · Confidence: {confidence if confidence is not None else "n/a"}</div></div>', unsafe_allow_html=True)
                st.caption(f"{vector_count:,} indexed passages")
                if "could not find" in (answer or "").lower() or evidence_status == "uncertain":
                    st.warning("ProofLoop refused or qualified this answer because the evidence was insufficient.")
                else:
                    st.success("Answer grounded in retrieved evidence.")
            except Exception as exc:
                st.error(f"ProofLoop failed: {exc}")
    else:
        st.markdown('<div class="answer-card" style="margin-top:1rem;color:#66788c">Your grounded answer will appear here, together with the retrieval path used to produce it.</div>', unsafe_allow_html=True)

with right.container(border=True):
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Evidence sources</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-subtitle">Sources selected for the current answer</div>', unsafe_allow_html=True)

    if run and 'evidence' in locals() and evidence:
        for index, item in enumerate(evidence, 1):
            organization, category = display_metadata(item)
            source = item.get("source", "unknown")
            page = item.get("page", "?")
            excerpt = clean_text(item.get("excerpt", ""))
            st.markdown(f'<div class="source-card"><div class="source-title">{index}. {organization} · Page {page}</div><div class="source-meta">{category} · {source}</div><div class="source-text">{excerpt}</div><span class="pill">Evidence</span></div>', unsafe_allow_html=True)
    else:
        st.info("Run a question to see the cited source cards here.")


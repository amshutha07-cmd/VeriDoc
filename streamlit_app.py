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

header_left, header_right = st.columns([1, 1])
with header_left:
    st.markdown("## ◉ ProofLoop")
with header_right:
    st.markdown("<div style='text-align:right; color:#9db4ca; padding-top:.55rem;'>Evidence-first document intelligence</div>", unsafe_allow_html=True)

left, center, right = st.columns([1.08, 2.55, 1.42], gap="large")

with left.container(border=True):
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


st.markdown("""
<style>
/* Final ProofLoop dark theme override */
.stApp, [data-testid="stAppViewContainer"] { background:#07111f !important; color:#e7eef7 !important; }
[data-testid="stHeader"] { background:#07111f !important; }
.block-container { max-width:1500px !important; padding:1.25rem 2rem 3rem !important; }
[data-testid="stSidebar"] { background:#0b1628 !important; border-right:1px solid #203752 !important; }
[data-testid="stSidebar"] * { color:#d9e6f4 !important; }

.topbar { min-height:62px !important; height:auto !important; overflow:visible !important; display:flex !important; align-items:center !important; padding:1rem 1.4rem !important; background:#0b1b31 !important; border:1px solid #244463 !important; border-radius:14px !important; margin:0 0 1.1rem !important; }
.brand { color:#ffffff !important; font-size:1.35rem !important; line-height:1.25 !important; white-space:nowrap !important; }
.brand-mark { color:#56d6c7 !important; }
.top-status { color:#a9bfd6 !important; line-height:1.3 !important; }

[data-testid="stVerticalBlockBorderWrapper"] { background:#0c1b2d !important; border:1px solid #264968 !important; border-radius:14px !important; padding:.85rem !important; min-height:0 !important; }
[data-testid="stVerticalBlockBorderWrapper"] > div { min-height:0 !important; }

.panel-title, h1, h2, h3, label, .stMarkdown { color:#e7eef7 !important; }
.panel-subtitle, .stCaption { color:#91a9c1 !important; }

.chat-panel { background:#0c1b2d !important; color:#e7eef7 !important; border:0 !important; min-height:0 !important; padding:0 !important; }
.chat-panel h3, .question-label { color:#ffffff !important; }
.answer-card { background:#f4f8fc !important; color:#1a2a3e !important; border-radius:12px !important; padding:1rem 1.1rem !important; }
.user-bubble { background:#1b527c !important; color:#ffffff !important; border-radius:12px !important; padding:.8rem 1rem !important; }
.trace-card { background:#112945 !important; border:1px solid #315777 !important; color:#d1e1ef !important; border-radius:12px !important; }
.trace-title { color:#ffffff !important; }
.trace-step { background:#1a496b !important; color:#bceee5 !important; }

/* Fix Streamlit uploader rendering */
[data-testid="stFileUploader"] { background:#0f2239 !important; border:1px dashed #4b7698 !important; border-radius:12px !important; padding:.45rem !important; }
[data-testid="stFileUploader"] section { background:#0f2239 !important; border:0 !important; }
[data-testid="stFileUploader"] section > div { color:#d9e6f4 !important; }
[data-testid="stFileUploader"] small { color:#9db4ca !important; }
[data-testid="stFileUploader"] button { background:#1b527c !important; color:#ffffff !important; border:1px solid #4d83a8 !important; }

.stButton button { background:#167f9a !important; color:#ffffff !important; border:1px solid #2ea9ad !important; border-radius:10px !important; font-weight:750 !important; }
.stButton button:hover { background:#1c9a9c !important; }
[data-testid="stTextArea"] textarea { background:#10243b !important; color:#e7eef7 !important; border:1px solid #42647f !important; border-radius:11px !important; }
[data-testid="stTextArea"] textarea::placeholder { color:#8da5ba !important; }

.source-card, .evidence-card { background:#10233a !important; border:1px solid #2e5270 !important; color:#dce8f3 !important; border-radius:11px !important; padding:.8rem !important; margin:.55rem 0 !important; box-shadow:none !important; }
.source-title, .evidence-source { color:#65d8c7 !important; }
.source-meta, .evidence-excerpt, .source-text { color:#b6c8da !important; }
.pill { background:#174f55 !important; color:#a9eee2 !important; }
[data-testid="stAlert"] { border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Final composition pass: full-page dark research workspace */
.stApp {
    background:
        radial-gradient(circle at 8% 12%, rgba(36,137,164,.16) 0, rgba(36,137,164,0) 24rem),
        radial-gradient(circle at 92% 22%, rgba(92,72,180,.14) 0, rgba(92,72,180,0) 28rem),
        #07111f !important;
    min-height:100vh !important;
}

/* Abstract background shapes, intentionally soft and non-rectangular. */
[data-testid="stAppViewContainer"]::before {
    content:"";
    position:fixed;
    width:320px;
    height:320px;
    right:-130px;
    bottom:80px;
    border-radius:48% 52% 63% 37% / 43% 38% 62% 57%;
    background:rgba(21,151,157,.08);
    filter:blur(2px);
    pointer-events:none;
    z-index:0;
}
[data-testid="stAppViewContainer"]::after {
    content:"";
    position:fixed;
    width:230px;
    height:230px;
    left:-100px;
    top:190px;
    border-radius:61% 39% 46% 54% / 45% 58% 42% 55%;
    background:rgba(72,92,192,.09);
    filter:blur(3px);
    pointer-events:none;
    z-index:0;
}

.main .block-container {
    max-width:1500px !important;
    width:calc(100% - 4rem) !important;
    margin:0 auto !important;
    padding:1.6rem 0 4rem !important;
    position:relative;
    z-index:1;
}

.topbar {
    width:100% !important;
    min-height:72px !important;
    box-sizing:border-box !important;
    display:flex !important;
    align-items:center !important;
    justify-content:space-between !important;
    gap:1rem !important;
    overflow:visible !important;
    padding:1rem 1.6rem !important;
    margin:0 0 1.4rem !important;
    border:1px solid #294b6b !important;
    border-radius:18px !important;
    background:linear-gradient(105deg,#0e2742 0%,#0b1a30 62%,#112c47 100%) !important;
    box-shadow:0 12px 32px rgba(0,0,0,.24) !important;
}
.brand {
    display:flex !important;
    align-items:center !important;
    gap:.55rem !important;
    color:#ffffff !important;
    font-size:1.5rem !important;
    font-weight:850 !important;
    line-height:1.3 !important;
    white-space:nowrap !important;
    overflow:visible !important;
}
.brand-mark {
    display:inline-block !important;
    color:#62e0d0 !important;
    font-size:1.35rem !important;
    line-height:1 !important;
}
.top-status {
    color:#afc7dc !important;
    font-size:.84rem !important;
    line-height:1.35 !important;
    white-space:nowrap !important;
}

[data-testid="column"] {
    min-width:0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    min-height:0 !important;
    height:auto !important;
    padding:1.05rem !important;
    border-radius:18px !important;
    background:rgba(12,27,45,.94) !important;
    border:1px solid #294b6b !important;
    box-shadow:0 12px 28px rgba(0,0,0,.14) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    min-height:0 !important;
}

/* Better rhythm between Streamlit blocks. */
[data-testid="stVerticalBlock"] > [data-testid="element-container"] {
    margin-bottom:.35rem !important;
}
.stMarkdown { line-height:1.5 !important; }

/* Keep uploader visible, shaped, and comfortably padded. */
[data-testid="stFileUploader"] {
    margin:.4rem 0 .8rem !important;
    padding:.7rem !important;
    min-height:112px !important;
    border-radius:16px !important;
    background:linear-gradient(145deg,#112b47,#0e2037) !important;
    border:1px dashed #4b829e !important;
}
[data-testid="stFileUploader"] section {
    min-height:92px !important;
    background:transparent !important;
}
[data-testid="stFileUploader"] section > div {
    color:#c9d9e8 !important;
}

/* The center becomes the visual focal point. */
.chat-panel {
    min-height:0 !important;
    padding:.15rem !important;
}
.chat-panel .answer-card {
    margin-top:1rem !important;
    min-height:130px !important;
}
.trace-card {
    margin-top:1rem !important;
    padding:1rem 1.1rem !important;
}

.source-card, .evidence-card {
    margin:.72rem 0 !important;
    padding:.9rem !important;
    border-radius:14px !important;
}

@media (max-width: 900px) {
    .main .block-container { width:calc(100% - 1.5rem) !important; padding-top:1rem !important; }
    .topbar { align-items:flex-start !important; flex-direction:column !important; }
    .top-status { white-space:normal !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Native header sizing: no clipped raw HTML wrapper */
.main h2 {
    color:#ffffff !important;
    font-size:1.55rem !important;
    line-height:1.35 !important;
    margin:.15rem 0 1rem !important;
    padding:0 !important;
}
[data-testid="column"]:has(h2) {
    min-height:48px !important;
}
</style>
""", unsafe_allow_html=True)

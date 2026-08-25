"""ProofLoop Streamlit interface.

The UI calls the existing FastAPI /ask SSE endpoint and renders:
- streamed graph trace
- supported/refused status
- source/page evidence cards
- retry count and confidence
"""

import json
import time
import uuid

import requests
import streamlit as st


st.set_page_config(
    page_title="ProofLoop | Evidence-First CRAG",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .stApp {
        background: #07111f;
        color: #edf5ff;
    }
    .block-container {
        max-width: 1280px;
        padding-top: 2rem;
    }
    .hero {
        padding: 1.8rem 2rem;
        border: 1px solid #1f3b5c;
        border-radius: 18px;
        background: linear-gradient(135deg, #0d2138 0%, #102d49 55%, #123a55 100%);
        margin-bottom: 1.3rem;
    }
    .hero h1 {
        color: #ffffff;
        font-size: 2.45rem;
        margin: 0 0 .35rem 0;
        letter-spacing: -0.04em;
    }
    .hero p {
        color: #b9d2e9;
        font-size: 1.03rem;
        margin: 0;
    }
    .metric-card {
        border: 1px solid #234463;
        border-radius: 12px;
        background: #0c1b2d;
        padding: .85rem 1rem;
        min-height: 74px;
    }
    .metric-label {
        color: #8eabc5;
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .08em;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: .25rem;
    }
    .trace-step {
        border-left: 3px solid #35b6a5;
        padding: .55rem .8rem;
        margin: .35rem 0;
        background: #0c1b2d;
        border-radius: 0 8px 8px 0;
    }
    .trace-step.rewrite {
        border-left-color: #e3a64b;
    }
    .evidence-card {
        border: 1px solid #2b5273;
        border-radius: 12px;
        background: #0b1a2b;
        padding: 1rem;
        margin: .6rem 0;
    }
    .evidence-source {
        color: #65d6c4;
        font-weight: 700;
        font-size: .92rem;
    }
    .evidence-excerpt {
        color: #c2d4e6;
        line-height: 1.55;
        margin-top: .55rem;
    }
    .status-supported {
        color: #58d6b5;
        font-weight: 700;
    }
    .status-refused {
        color: #ffb86b;
        font-weight: 700;
    }
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
    backend_url = st.text_input(
        "FastAPI backend URL",
        value="http://127.0.0.1:8000",
        help="Start Uvicorn separately before submitting a question.",
     ).rstrip("/")
    st.markdown("---")
    st.markdown("### What ProofLoop shows")
    st.write("The answer is generated only after retrieval is reranked and graded. Weak evidence can trigger a query rewrite. Unsupported questions are refused instead of being invented.")
    st.markdown("---")
    st.caption("Current corpus: corporate filings, macroeconomic reports, and educational references.")


question = st.text_area(
    "Ask a question about the indexed documents",
    value="What are Apple's main risk factors?",
    height=90,
    placeholder="Example: What are NVIDIA's major business risks?",
)

col_a, col_b = st.columns([1, 5])
with col_a:
    ask_clicked = st.button("Run ProofLoop", type="primary", use_container_width=True)
with col_b:
    st.caption("Try a supported question, then test refusal with: What was Apple's exact stock buyback amount in Q3 2019?")


if ask_clicked:
    if not question.strip():
        st.warning("Enter a question first.")
        st.stop()

    trace = []
    evidence = []
    answer = ""
    grade = ""
    evidence_status = ""
    confidence = None
    retries = 0
    error_message = None

    trace_placeholder = st.empty()
    answer_placeholder = st.empty()
    metrics_placeholder = st.empty()
    evidence_placeholder = st.empty()

    thread_id = f"streamlit-{uuid.uuid4().hex[:12]}"

    try:
        with st.spinner("Running the corrective retrieval loop..."):
            response = requests.post(
                f"{backend_url}/ask",
                json={"question": question.strip(), "thread_id": thread_id},
                stream=True,
                timeout=(10, 300),
            )
            response.raise_for_status()

            pending_event = None
            pending_data = []

            for raw_line in response.iter_lines(decode_unicode=True):
                line = raw_line.strip() if raw_line else ""

                if line.startswith("event:"):
                    pending_event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    pending_data.append(line.split(":", 1)[1].strip())
                elif not line and pending_data:
                    raw_data = "\n".join(pending_data)
                    pending_data = []

                    try:
                        payload = json.loads(raw_data)
                    except json.JSONDecodeError:
                        pending_event = None
                        continue

                    if pending_event == "error":
                        error_message = payload.get("message", "Unknown backend error")
                        break

                    if pending_event == "node":
                        node_name = payload.get("node", "unknown")
                        trace.append(node_name)

                        if payload.get("answer"):
                            answer = payload["answer"]
                        if payload.get("grade"):
                            grade = payload["grade"]
                        if payload.get("retries") is not None:
                            retries = payload["retries"]
                        if payload.get("evidence_status"):
                            evidence_status = payload["evidence_status"]
                        if payload.get("evidence_confidence") is not None:
                            confidence = payload["evidence_confidence"]
                        if payload.get("evidence"):
                            evidence = payload["evidence"]

                        trace_html = []
                        for step in trace:
                            css_class = "trace-step rewrite" if step == "rewrite" else "trace-step"
                            trace_html.append(
                                f'<div class="{css_class}"><strong>{step}</strong> completed</div>'
                            )
                        trace_placeholder.markdown(
                            "### Retrieval Trace\n" + "".join(trace_html),
                            unsafe_allow_html=True,
                        )

                        if answer:
                            answer_placeholder.markdown("### Answer\n" + answer)

                        metrics_placeholder.empty()
                        metric_cols = metrics_placeholder.columns(4)
                        metric_cols[0].markdown(
                            f'<div class="metric-card"><div class="metric-label">Support</div><div class="metric-value">{evidence_status or "pending"}</div></div>',
                            unsafe_allow_html=True,
                        )
                        metric_cols[1].markdown(
                            f'<div class="metric-card"><div class="metric-label">Grade</div><div class="metric-value">{grade or "pending"}</div></div>',
                            unsafe_allow_html=True,
                        )
                        metric_cols[2].markdown(
                            f'<div class="metric-card"><div class="metric-label">Retries</div><div class="metric-value">{retries}</div></div>',
                            unsafe_allow_html=True,
                        )
                        metric_cols[3].markdown(
                            f'<div class="metric-card"><div class="metric-label">Confidence</div><div class="metric-value">{confidence if confidence is not None else "pending"}</div></div>',
                            unsafe_allow_html=True,
                        )

                        if evidence:
                            cards = ["### Evidence"]
                            for item in evidence:
                                source = item.get("source", "unknown")
                                page = item.get("page", "?")
                                excerpt = item.get("excerpt", "")
                                support = item.get("support", "direct")
                                cards.append(
                                    f'<div class="evidence-card"><div class="evidence-source">{source} · Page {page} · {support}</div><div class="evidence-excerpt">{excerpt}</div></div>'
                                )
                            evidence_placeholder.markdown("\n".join(cards), unsafe_allow_html=True)

                    pending_event = None

    except requests.exceptions.ConnectionError:
        error_message = f"Could not connect to {backend_url}. Start FastAPI first with Uvicorn."
    except requests.exceptions.Timeout:
        error_message = "The backend request timed out. The graph may still be loading its models or processing the corpus."
    except requests.exceptions.RequestException as exc:
        error_message = f"Backend request failed: {exc}"
    except Exception as exc:
        error_message = f"Unexpected UI error: {exc}"

    if error_message:
        st.error(error_message)
    elif answer:
        if "could not find" in answer.lower() or evidence_status == "uncertain":
            st.warning("ProofLoop refused or qualified this answer because the retrieved evidence was insufficient.")
        else:
            st.success("Answer generated from retrieved evidence.")

else:
    st.info("Enter a question and select Run ProofLoop to see the live retrieval trace and evidence cards.")

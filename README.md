# VeriDoc

**An evidence-first Corrective RAG system with a bounded self-correction loop, cross-encoder reranking and grounded refusal.**

VeriDoc answers questions over PDF and DOCX corpora, and it treats retrieval quality as something to be measured rather than assumed. A LangGraph state machine grades the retrieved evidence before generation. Weak evidence triggers a query rewrite and a second retrieval pass. If the evidence is still insufficient after the retry budget is spent, the system refuses instead of hallucinating. Every answer carries source and page-level provenance, and the full retrieval trace is exposed in the UI.

**Live demo:** https://veridoc-phi.vercel.app

![VeriDoc answering a question with citations and 2 correction retries](docs/demo.png)

## Features

- Answers with source file and page citations, and shows the passage each claim came from
- Grades its own evidence before answering
- Rewrites weak queries and retries (up to 2 times)
- Refuses when the documents don't support the question
- Upload your own PDF or DOCX files and ask questions about them
- Shows the full retrieval trace (retries, grading, sources) in the UI

## Architecture

```mermaid
flowchart LR
    Q[Query] --> R[Dense retrieval]
    R --> RR[Cross-encoder rerank]
    RR --> G{Evidence grader}
    G -->|sufficient| GEN[Grounded generation + citations]
    G -->|weak, retries left| RW[Query rewrite]
    RW --> R
    G -->|weak, budget exhausted| REF[Grounded refusal]

    subgraph Index
      D[PDF / DOCX] --> L[Page-aware loader]
      L --> C[Chunker]
      C --> E1[MiniLM-L6-v2, 384-d]
      C --> E2[text-embedding-3-small, 1536-d]
      E1 --> V1[(Chroma: handbook)]
      E2 --> V2[(Chroma: legal)]
    end
    V1 --> R
    V2 --> R
```

| Stage | What happens |
|---|---|
| Retrieve | Dense vector search over ChromaDB for candidate chunks |
| Rerank | A cross-encoder re-scores each query-passage pair and keeps the best few |
| Grade | Checks whether the evidence is actually enough to answer |
| Rewrite | Rewrites the query and retries, up to 2 times |
| Generate | Answers only from the evidence, with source and page citations |
| Refuse | Says the question isn't supported if proof still isn't found |

## Data

Input is PDF and DOCX files, loaded page by page and split into chunks. Two ChromaDB collections are indexed: a handbook collection (~20k chunks from company filings, economic reports and educational material) and a legal collection (~1.4k chunks of Indian law). Users can also upload their own documents.

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| API | FastAPI, slowapi (rate limiting) |
| Vector store | ChromaDB |
| Embeddings | all-MiniLM-L6-v2 (local), text-embedding-3-small (via OpenRouter) |
| Reranker | Sentence Transformers cross-encoder |
| LLM gateway | OpenRouter |
| Frontend | Vite (Ask, Registry, Graph, Ingest, Evals) |
| Infrastructure | Docker, Google Cloud Run, Vercel |

## Deployment

The frontend is hosted on Vercel and the backend runs as a Docker container on Google Cloud Run (`asia-south1`). The frontend calls the backend over HTTP, and the backend only accepts requests from allowed origins (CORS allowlist).

## Run locally

```bash
# backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
export OPENROUTER_API_KEY=<your-key>
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

## Limitations

- Portfolio prototype with no authentication or per-user isolation, so only upload public, non-sensitive documents.
- The first request after idle time is slow (cold start).
- Answers are limited to what is in the indexed documents; anything outside is refused by design.
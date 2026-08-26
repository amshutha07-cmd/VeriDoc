"""
FastAPI entrypoint — wires ingest, ask (SSE), and health routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_ingest import router as ingest_router
from app.api.routes_ask import router as ask_router

app = FastAPI(title="Self-Correcting RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your Vercel domain once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(ask_router)


@app.get("/health")
def health():
    return {"status": "ok"}
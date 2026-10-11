import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.api.routes_ingest import router as ingest_router
from app.api.routes_ask import router as ask_router
from app.api.routes_graph import router as graph_router
from app.api.routes_eval import router as eval_router
app = FastAPI(title="Self-Correcting RAG API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(ask_router)
app.include_router(graph_router)
app.include_router(eval_router)


@app.get("/health")
def health():
    return {"status": "ok"}

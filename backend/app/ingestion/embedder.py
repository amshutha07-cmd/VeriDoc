"""Embedding providers for the separate corporate and Indian-law collections."""

from app.core.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings():
    """Embedding provider for the Indian-law collection: 1536 dimensions."""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        check_embedding_ctx_length=False,
     )


def get_corporate_embeddings():
    """Embedding provider matching the existing 384-dimensional handbook index."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

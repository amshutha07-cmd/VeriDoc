"""
Metadata-aware embedding provider for VeriDoc Nexus.
Configured to use OpenRouter to bypass rate limits and scale ingestion.
"""
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings

def get_embeddings():
    """
    Returns an embeddings object.
    Switched to OpenRouter (OpenAI-compatible) to handle large datasets
    without the Gemini free-tier rate limits.
    """
    # We use the OpenAIEmbeddings class but point it to OpenRouter
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        # Disabling context length check as OpenRouter handles various models
        check_embedding_ctx_length=False
    )

if __name__ == "__main__":
    # Test the OpenRouter embedding connection
    try:
        embeddings = get_embeddings()
        test_text = "What is the capital of France?"
        vec = embeddings.embed_query(test_text)
        print(f"âœ… OpenRouter Connection Successful")
        print(f"Embedding dimensions: {len(vec)}")
    except Exception as e:
        print(f"âŒ Connection Failed: {e}")

# """
# Module 1c — Embed
# Factory for turning chunks into vectors. Same model MUST be used for
# indexing and querying — swapping models means reindexing everything.
# """
# from app.core.config import settings


# def get_embeddings():
#     """
#     Returns an embeddings object based on settings.embedding_provider.
#     - "openai"     -> text-embedding-3-small (paid, fast, 1536-dim)
#     - "huggingface" -> BAAI/bge-small-en-v1.5 (free, fully local)
#     """
#     if settings.embedding_provider == "huggingface":
#         from langchain_huggingface import HuggingFaceEmbeddings
#         return HuggingFaceEmbeddings(model_name=settings.embedding_model_hf)

#     from langchain_openai import OpenAIEmbeddings
#     return OpenAIEmbeddings(
#         model=settings.embedding_model_openai,
#         api_key=settings.openai_api_key,
#     )


# if __name__ == "__main__":
#     embeddings = get_embeddings()
#     vec = embeddings.embed_query("What is the refund policy")
#     print(f"Embedding dimensions: {len(vec)}")
"""
Module 1c — Embed
Factory for turning chunks into vectors. Same model MUST be used for
indexing and querying — swapping models means reindexing everything.
"""
from app.core.config import settings


def get_embeddings():
    """
    Returns an embeddings object based on settings.embedding_provider.
    - "gemini"      -> text-embedding-004 (free tier, hosted, deploy-ready)
    - "openai"      -> text-embedding-3-small (paid, fast, 1536-dim)
    - "huggingface" -> BAAI/bge-small-en-v1.5 (free, fully local)
    """
    if settings.embedding_provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model_gemini,
            google_api_key=settings.google_api_key,
        )

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.embedding_model_hf)

    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=settings.embedding_model_openai,
        api_key=settings.openai_api_key,
    )


if __name__ == "__main__":
    embeddings = get_embeddings()
    vec = embeddings.embed_query("What is the refund policy")
    print(f"Embedding dimensions: {len(vec)}")
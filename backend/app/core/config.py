# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", extra="ignore")

#     # LLM / embeddings
#     openrouter_api_key: str = Field(default="")
#     openai_api_key: str = Field(default="")
#     google_api_key: str = Field(default="")
#     google_api_key_2: str = Field(default="")
#     embedding_provider: str = Field(default="gemini")
#     embedding_model_openai: str = "text-embedding-3-small"
#     embedding_model_hf: str = "BAAI/bge-small-en-v1.5"
#     embedding_model_gemini: str = "gemini-embedding-001"

#     # LLM (chat/reasoning)
#     llm_model: str = "gemini-3.7-flash"
#     max_retries: int = 2
#     rerank_top_n: int = 4

#     # chunking
#     chunk_size: int = 800
#     chunk_overlap: int = 120

#     # retrieval
#     retrieve_k: int = 12
#     retrieve_fetch_k: int = 40

#     # paths
#     data_dir: str = "./data"
#     chroma_persist_dir: str = "./chroma_db"
#     chroma_collection_name: str = "handbook"


# settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM / embeddings
    openrouter_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    google_api_key: str = Field(default="")
    google_api_key_2: str = Field(default="")
    embedding_provider: str = Field(default="gemini")
    embedding_model_openai: str = "text-embedding-3-small"
    embedding_model_hf: str = "BAAI/bge-small-en-v1.5"
    embedding_model_gemini: str = "gemini-embedding-001"

    # LLM (chat/reasoning)
    llm_model: str = "gemini-3.7-flash"
    max_retries: int = 2
    rerank_top_n: int = 4

    # chunking
    chunk_size: int = 800
    chunk_overlap: int = 120

    # retrieval
    retrieve_k: int = 12
    retrieve_fetch_k: int = 40

    # paths
    data_dir: str = "./data"
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "handbook"


settings = Settings()
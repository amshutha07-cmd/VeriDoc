# """
# Shared LLM client — one Gemini chat model instance reused across
# Grade, Rewrite, and Generate nodes. Initialized once at import time,
# same reuse pattern as the vector store in Module 3.
# """
# from langchain_google_genai import ChatGoogleGenerativeAI
# from app.core.config import settings
# import warnings
# warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

# from langchain_openai import ChatOpenAI
# from app.core.config import settings

# llm = ChatOpenAI(
#     model="stealth/ox-alpha",
#     openai_api_key=settings.openrouter_api_key,
#     openai_api_base="https://openrouter.ai/api/v1",
#     temperature=0,
#     max_retries=3,
# )
# llm_fallback = None
# if settings.google_api_key_2:
#     llm_fallback = ChatGoogleGenerativeAI(
#         model=settings.llm_model,
#         google_api_key=settings.google_api_key_2,
#         temperature=0,
#         max_retries=3,
#     )
# llm = ChatGoogleGenerativeAI(
#     model=settings.llm_model,
#     google_api_key=settings.google_api_key,
#     temperature=0,   # deterministic — right default for grading/rewriting/factual QA
# )
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

from langchain_openai import ChatOpenAI
from app.core.config import settings

llm = ChatOpenAI(
    model="stealth/ox-alpha",
    openai_api_key=settings.openrouter_api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0,
    max_retries=3,
)
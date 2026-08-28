import os
import time
from typing import Any

from langchain_openai import ChatOpenAI
from app.core.config import settings


DEFAULT_MODELS = [
    "z-ai/glm-5.3-flash",
    "openai/gpt-4o-mini",
    "google/gemini-2.5-flash",
    "openrouter/free",
]


def _model_chain() -> list[str]:
    configured = os.getenv("VERIDOC_MODELS", "")
    models = [item.strip() for item in configured.split(",") if item.strip()]
    return models or DEFAULT_MODELS


def _response_text(response: Any) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return " ".join(parts).strip()
    return str(content or "").strip()


def _is_fallback_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(token in message for token in (
        "402", "404", "409", "429", "500", "502", "503", "504",
        "insufficient credits", "rate limit", "not found", "unavailable",
        "overloaded", "timeout", "timed out", "temporarily",
    ))


class FallbackChatModel:
    def __init__(self) -> None:
        key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "No OpenRouter API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
            )

        self.models = _model_chain()
        self.clients = [
            ChatOpenAI(
                model=model,
                api_key=key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0,
                max_retries=0,
             )
            for model in self.models
        ]
        self.last_model = None

    def invoke(self, prompt: Any, *args: Any, **kwargs: Any) -> Any:
        failures = []

        for model, client in zip(self.models, self.clients):
            try:
                response = client.invoke(prompt, *args, **kwargs)
                text = _response_text(response)
                if not text:
                    raise RuntimeError("The model returned an empty response")

                self.last_model = model
                print(f"LLM model used: {model}")
                return response

            except Exception as error:
                failures.append(f"{model}: {type(error).__name__}: {error}")
                print(f"LLM fallback: {model} failed; trying next model")

                # A 401 almost always means the key is invalid. Trying other
                # models would repeat the same authentication failure.
                if "401" in str(error) or "authentication" in str(error).lower():
                    break

                if not _is_fallback_error(error):
                    break

                time.sleep(0.25)

        details = " | ".join(failures)
        raise RuntimeError(f"All configured LLM models failed. {details}")


llm = FallbackChatModel()


def get_llm() -> FallbackChatModel:
    return llm

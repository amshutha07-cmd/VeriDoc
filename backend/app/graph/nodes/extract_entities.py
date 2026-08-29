import re
from typing import Any, Dict
from app.graph.llm_client import get_llm
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def extract_entities(state: dict):
    # Fallback to Gemini Free for extraction to bypass OpenRouter 402
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.google_api_key)
    question = state["question"]
    
    prompt = f"Extract corporate entities (Company, Year) from: '{question}'. Return: Company: X, Year: Y."
    response = llm.invoke(prompt)
    
    entities = []
    if "None" not in response.content:
        for item in str(response.content).split(","):
            entities.append({"text": item.strip()})
    return {"entities": entities}

    llm = get_llm()
    prompt = f"""Extract key corporate entities (Company, Year, Metric, Risk) from this question:
'{question}'
Return only a comma-separated list like: Company: NVIDIA, Year: 2023, Metric: Net Income.
If none, return 'None'."""
    response = llm.invoke(prompt)
    entities = []
    content = str(response.content)
    if "None" not in content:
        for item in content.split(","):
            entities.append({"text": item.strip()})
    return {"entities": entities}

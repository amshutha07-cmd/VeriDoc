from typing import Any, Dict
from app.graph.llm_client import get_llm

def extract_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state["question"]
    llm = get_llm() # Using the helper function

    prompt = f"""Extract key corporate entities (Company, Year, Metric, Risk) from this question:
    '{question}'
    Return only a comma-separated list like: Company: NVIDIA, Year: 2023, Metric: Net Income.
    If none, return 'None'."""

    response = llm.invoke(prompt)
    entities = []
    if "None" not in response.content:
        for item in response.content.split(","):
            entities.append({"text": item.strip()})

    return {"entities": entities}

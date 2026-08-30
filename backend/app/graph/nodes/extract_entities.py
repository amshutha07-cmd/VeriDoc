from app.graph.llm_client import get_llm


def extract_entities(state: dict):
    question = state.get("question", "")
    domain = state.get("domain", "")

    if domain == "indian_law":
        prompt = f"""Extract key legal entities (Act, Section, Article, Body such as Gram Sabha or Committee) from this question:
'{question}'
Return only a comma-separated list like: Act: Forest Rights Act, Section: 3, Body: Gram Sabha.
If none, return 'None'."""
    else:
        prompt = f"""Extract key corporate entities (Company, Year, Metric, Risk) from this question:
'{question}'
Return only a comma-separated list like: Company: NVIDIA, Year: 2023, Metric: Net Income.
If none, return 'None'."""

    try:
        response = get_llm().invoke(prompt)
        content = str(response.content).strip()
    except Exception:
        # Entity extraction is auxiliary; retrieval and answer generation can continue.
        return {"entities": []}

    entities = []
    if content and content.lower() != "none":
        for item in content.split(","):
            value = item.strip()
            if value:
                entities.append({"text": value})
    return {"entities": entities}
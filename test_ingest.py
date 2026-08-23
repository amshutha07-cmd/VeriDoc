import requests

with open("data/aapl-20250927.pdf", "rb") as f:
    response = requests.post(
        "http://127.0.0.1:8000/ingest",
        files={"files": ("aapl-20250927.pdf", f, "application/pdf")},
    )

print(response.status_code)
print(response.json())
import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/ask",
    json={"question": "What are Apple's main risk factors?", "thread_id": "test-1"},
    stream=True,
)

for line in response.iter_lines():
    if line:
        decoded = line.decode("utf-8")
        print(decoded)
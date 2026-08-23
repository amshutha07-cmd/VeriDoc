from app.graph.llm_client import llm

response = llm.invoke("say hi")
print(response.content)
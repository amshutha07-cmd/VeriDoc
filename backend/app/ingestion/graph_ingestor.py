from app.graph_store.graph_handler import VeriDocGraph
from app.graph.nodes.extract_entities import extract_entities

def ingest_to_graph(company_name, doc_name, text_chunks):
    graph = VeriDocGraph()

    # 1. Add core nodes
    graph.add_entity(company_name, "Company")
    graph.add_entity(doc_name, "Document")

    # 2. Connect company to document
    graph.add_relationship(company_name, doc_name, "FILED")

    # 3. Simple relationship extraction (placeholder for LLM extraction)
    for chunk in text_chunks[:5]: # Take first few chunks to build initial connections
        # In a full build, we'd use an LLM here to find Risks/Metrics
        # For now, let's link chunks to the document
        pass

    graph.save()
    print(f"âœ… Graph updated for {company_name}")

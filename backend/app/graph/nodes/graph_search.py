from app.graph_store.graph_handler import VeriDocGraph

def graph_search(state: dict):
    """Hybrid Node: Combines Graph Traversal with Vector Context."""
    entities = state.get("entities", [])
    graph = VeriDocGraph()
    nexus_context = []

    for ent in entities:
        # Perform a 2-hop search (The 'Amazing' part)
        connections = graph.get_nexus_connections(ent["text"], depth=2)
        for conn in connections:
            node_data = graph.graph.nodes[conn]
            nexus_context.append(f"Entity: {conn} ({node_data.get('type')})")

    return {"graph_results": nexus_context}

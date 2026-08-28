import networkx as nx
import os, pickle

class VeriDocGraph:
    def __init__(self, storage_path="backend/data/graph_store.pkl"):
        self.storage_path = storage_path
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_entity(self, entity_id, entity_type, properties=None):
        self.graph.add_node(entity_id, type=entity_type, **(properties or {}))

    def add_relationship(self, source, target, rel_type, properties=None):
        self.graph.add_edge(source, target, key=rel_type, rel_type=rel_type, **(properties or {}))

    def get_nexus_connections(self, entity_name, depth=2):
        """AMAZING FEATURE: Finds multi-hop connections human investigators miss."""
        if entity_name not in self.graph:
            return []
        # Finds everything connected to the company, and everything connected to those things.
        return list(nx.single_source_shortest_path_length(self.graph, entity_name, cutoff=depth).keys())

    def save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'wb') as f:
            pickle.dump(self.graph, f)

    def load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'rb') as f:
                self.graph = pickle.load(f)

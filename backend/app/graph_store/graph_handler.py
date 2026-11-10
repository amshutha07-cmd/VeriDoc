import json
import os

import networkx as nx


class VeriDocGraph:
    def __init__(self, storage_path="backend/data/graph_store.json"):
        self.storage_path = storage_path
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_entity(self, entity_id, entity_type, properties=None):
        self.graph.add_node(entity_id, type=entity_type, **(properties or {}))

    def add_relationship(self, source, target, rel_type, properties=None):
        self.graph.add_edge(source, target, key=rel_type, rel_type=rel_type, **(properties or {}))

    def get_nexus_connections(self, entity_name, depth=2):
        """Find multi-hop connections around an entity (everything within `depth` hops)."""
        if entity_name not in self.graph:
            return []
        return list(nx.single_source_shortest_path_length(self.graph, entity_name, cutoff=depth).keys())

    def save(self):
        directory = os.path.dirname(self.storage_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = self.storage_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(nx.node_link_data(self.graph, edges="edges"), f, ensure_ascii=False, default=str)
        os.replace(tmp_path, self.storage_path)

    def load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data, directed=True, multigraph=True, edges="edges")
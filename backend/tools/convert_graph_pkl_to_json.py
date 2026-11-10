"""One-off converter: graph_store.pkl -> graph_store.json.

Run this ONLY on a pickle you built yourself. Unpickling a file from anyone
else can execute arbitrary code, which is why the server no longer uses pickle.
"""
import json
import pickle
import sys

import networkx as nx

src, dst = sys.argv[1], sys.argv[2]
with open(src, "rb") as f:
    old = pickle.load(f)

with open(dst, "w", encoding="utf-8") as f:
    json.dump(nx.node_link_data(old, edges="edges"), f, ensure_ascii=False, default=str)

with open(dst, "r", encoding="utf-8") as f:
    new = nx.node_link_graph(json.load(f), directed=True, multigraph=True, edges="edges")

same = (
    old.number_of_nodes() == new.number_of_nodes()
    and old.number_of_edges() == new.number_of_edges()
    and dict(old.nodes(data=True)) == dict(new.nodes(data=True))
)
print(f"nodes {old.number_of_nodes()} -> {new.number_of_nodes()}, edges {old.number_of_edges()} -> {new.number_of_edges()}, identical: {same}")
sys.exit(0 if same else 1)
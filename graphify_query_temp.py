import json
from pathlib import Path
from collections import Counter

graph_path = Path("C:/Development/investing-algorithm-framework/graphify-out/graph.json")
graph = json.loads(graph_path.read_text(encoding="utf-8"))
print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['links'])}")

types = Counter(n.get("type", "unknown") for n in graph["nodes"])
print(f"Node types: {dict(types)}")

coms = Counter(n.get("community", -1) for n in graph["nodes"])
print(f"Communities: {dict(sorted(coms.items()))}")

labels_path = Path("C:/Development/investing-algorithm-framework/graphify-out/.graphify_labels.json")
if labels_path.exists():
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    print(f"Community labels: {labels}")

com_nodes = {}
for n in graph["nodes"]:
    c = n.get("community", -1)
    if c not in com_nodes:
        com_nodes[c] = []
    com_nodes[c].append(n.get("label", n.get("id", "?")))

for c in sorted(com_nodes.keys()):
    samples = com_nodes[c][:5]
    print(f"  Community {c}: {samples}...")

"""
TopHash TUDataset fetcher — real MUTAG, PROTEINS, NCI1.

These are the canonical graph classification benchmarks used in the graph
kernel literature. Real public data from www.chrsmrrs.com/graphkerneldatasets.

MUTAG: 188 graphs, 2 classes (125 mutagenic / 63 non-mutagenic)
  - Debnath et al. 1991. Nitroaromatic compounds.

PROTEINS: 1,113 graphs, 2 classes
  - Dobson & Doig 2003. Protein structure graphs.

NCI1: 4,110 graphs, 2 classes
  - Wale et al. 2008. Anti-cancer activity screens.
"""
import os
import sys
import pickle
import networkx as nx
import numpy as np
from typing import List, Tuple

DATA_ROOT = "/home/z/my-project/data"


def _tu_to_networkx(data) -> nx.Graph:
    """Convert a torch_geometric Data object to a networkx graph."""
    G = nx.Graph()
    edge_index = data.edge_index.numpy()
    n_nodes = data.num_nodes
    for i in range(n_nodes):
        # Use node features (atom type one-hot) as a label
        if data.x is not None:
            atom_type = int(np.argmax(data.x[i].numpy()))
        else:
            atom_type = 0
        G.add_node(i, atom_type=atom_type)
    # Edges (each edge appears twice in edge_index for undirected)
    for j in range(edge_index.shape[1]):
        u, v = int(edge_index[0, j]), int(edge_index[1, j])
        if u < v:  # avoid double-adding
            G.add_edge(u, v)
    return G


def fetch_tudataset(name: str) -> List[Tuple[nx.Graph, str]]:
    """
    Fetch a TUDataset by name. Returns list of (graph, label_string) tuples.

    name: 'MUTAG', 'PROTEINS', 'NCI1', etc.
    """
    print(f"\n  Fetching TUDataset: {name}")
    cache_file = os.path.join(DATA_ROOT, "tudataset", f"{name}_graphs.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
        print(f"    [cached] {len(data)} graphs from {cache_file}")
        return data

    try:
        from torch_geometric.datasets import TUDataset
        import torch
    except ImportError as e:
        print(f"    FAILED: torch_geometric not available ({e})")
        return []

    root = os.path.join(DATA_ROOT, "tudataset")
    os.makedirs(root, exist_ok=True)
    try:
        dataset = TUDataset(root=root, name=name)
    except Exception as e:
        print(f"    FAILED to download {name}: {e}")
        return []

    print(f"    {name}: {len(dataset)} graphs, {dataset.num_classes} classes")

    import collections
    labels = [int(d.y.item()) for d in dataset]
    label_counts = collections.Counter(labels)
    print(f"    Class distribution: {dict(label_counts)}")

    # Convert all to networkx
    data = []
    for i, d in enumerate(dataset):
        G = _tu_to_networkx(d)
        label = f"class_{int(d.y.item())}"
        data.append((G, label))

    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)
    print(f"    Saved {len(data)} networkx graphs to {cache_file}")
    return data


def fetch_all_tu() -> dict:
    """Fetch MUTAG, PROTEINS, NCI1."""
    print("=" * 70)
    print("TUDataset fetcher — real MUTAG / PROTEINS / NCI1")
    print("=" * 70)
    results = {}
    for name in ["MUTAG", "PROTEINS", "NCI1"]:
        data = fetch_tudataset(name)
        if data:
            results[name] = data
    print()
    print("SUMMARY:")
    for name, data in results.items():
        # Class balance
        from collections import Counter
        label_counts = Counter(l for _, l in data)
        majority_pct = max(label_counts.values()) / len(data) * 100
        print(f"  {name:10s}: {len(data):5d} graphs, classes={dict(label_counts)}, "
              f"majority class = {majority_pct:.1f}%")
    return results


if __name__ == "__main__":
    fetch_all_tu()

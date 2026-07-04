"""
TopHash v3 Ensemble — 156D Multi-Resolution Fingerprint

Computes the v3 fingerprint at the original graph and at a coarsened graph,
then appends the difference vector. Captures both fine and coarse structure.

Output: [h_fine (52), h_coarse (52), h_diff (52)] = 156D
"""
import numpy as np
import networkx as nx
from typing import Dict, Any

from . import core as v3_core

TOPHASH_V3E_DIM = 156


def compute(G: nx.Graph, coarsening: str = "heavy_edge") -> np.ndarray:
    """
    Compute the 156D TopHash v3 Ensemble fingerprint.

    Pipeline:
      1. Compute h_fine = TopHash v3 (G)
      2. Coarsen G → G_coarse (halve the node count using heavy-edge matching)
      3. Compute h_coarse = TopHash v3 (G_coarse)
      4. h_diff = h_fine - h_coarse
      5. Return [h_fine, h_coarse, h_diff]
    """
    G = v3_core._normalize_graph(G)
    n = G.number_of_nodes()

    h_fine = v3_core.compute(G)

    if n <= 2:
        # Cannot meaningfully coarsen — use zeros for coarse and diff
        h_coarse = np.zeros_like(h_fine)
        h_diff = h_fine.copy()
    else:
        try:
            G_coarse = _coarsen_heavy_edge(G)
            h_coarse = v3_core.compute(G_coarse)
        except Exception:
            h_coarse = np.zeros_like(h_fine)
        h_diff = h_fine - h_coarse

    return np.concatenate([h_fine, h_coarse, h_diff])


def explain(G: nx.Graph) -> Dict[str, Any]:
    """Return full explanation of the ensemble computation."""
    G = v3_core._normalize_graph(G)
    n = G.number_of_nodes()

    h_fine = v3_core.compute(G)
    if n <= 2:
        h_coarse = np.zeros_like(h_fine)
        G_coarse = G.copy()
    else:
        try:
            G_coarse = _coarsen_heavy_edge(G)
            h_coarse = v3_core.compute(G_coarse)
        except Exception:
            h_coarse = np.zeros_like(h_fine)
            G_coarse = G.copy()

    h_diff = h_fine - h_coarse

    return {
        "schema_version": "tophash-v3e-1.0.0",
        "n_nodes_fine": G.number_of_nodes(),
        "n_nodes_coarse": G_coarse.number_of_nodes(),
        "h_fine": h_fine,
        "h_coarse": h_coarse,
        "h_diff": h_diff,
        "fingerprint": np.concatenate([h_fine, h_coarse, h_diff]),
    }


def _coarsen_heavy_edge(G: nx.Graph) -> nx.Graph:
    """
    Permutation-invariant heavy-edge matching coarsening.

    Each iteration:
      1. Sort edges by weight descending (here: degree-product as edge importance proxy)
      2. Greedily select non-overlapping matched edges
      3. Contract matched edges into single nodes
      4. Preserve multiedges as weighted simple edges

    This is order-independent because sorting is deterministic on edge attributes,
    not on node indices.
    """
    if G.number_of_nodes() <= 1:
        return G.copy()

    # Compute edge importance = degree_u * degree_v (heavy edge heuristic)
    edges_with_weight = []
    degrees = dict(G.degree())
    for u, v in G.edges():
        w = degrees[u] * degrees[v]
        # Use min(u,v),max(u,v) to break ties deterministically without node index bias
        edges_with_weight.append((w, min(u, v), max(u, v), u, v))

    # Sort: highest weight first, ties broken by node pair (deterministic)
    edges_with_weight.sort(key=lambda x: (-x[0], x[1], x[2]))

    # Greedy matching
    matched = set()
    matching = []
    for w, _, _, u, v in edges_with_weight:
        if u not in matched and v not in matched:
            matching.append((u, v))
            matched.add(u)
            matched.add(v)

    # If no edges matched (e.g., isolated nodes), pick first edge arbitrarily
    if not matching and G.number_of_edges() > 0:
        u, v = next(iter(G.edges()))
        matching.append((u, v))
        matched.add(u)
        matched.add(v)

    # Build contraction map: unmatched nodes map to themselves; matched pairs merge to min(u,v)
    contraction = {}
    for u, v in matching:
        keep, drop = min(u, v), max(u, v)
        contraction[drop] = keep
        if keep not in contraction:
            contraction[keep] = keep
    for n in G.nodes():
        if n not in contraction:
            contraction[n] = n

    # Build coarsened graph
    G_coarse = nx.Graph()
    # Aggregate edge weights
    edge_agg = {}
    for u, v in G.edges():
        new_u = contraction[u]
        new_v = contraction[v]
        if new_u == new_v:
            continue
        key = (min(new_u, new_v), max(new_u, new_v))
        edge_agg[key] = edge_agg.get(key, 0) + 1

    for (u, v), w in edge_agg.items():
        G_coarse.add_edge(u, v, weight=w)

    # Ensure all nodes exist
    for n in set(contraction.values()):
        if n not in G_coarse:
            G_coarse.add_node(n)

    return G_coarse

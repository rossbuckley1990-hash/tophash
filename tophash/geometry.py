"""
TopHash v3 — Geometry / Statistics View (10D)

Computes geometric and combinatorial statistics of the graph.

Output dimensions (10):
  1. Mean degree (normalized)
  2. Std degree
  3. Max degree (normalized)
  4. Clustering coefficient (mean)
  5. Triangle count (normalized)
  6. Mean shortest path length
  7. Diameter (normalized)
  8. Density
  9. Assortativity (degree correlation)
  10. Motif count: 4-path count (normalized)
"""
import numpy as np
import networkx as nx


def compute_geometry_view(G: nx.Graph, label_attr: str = None) -> np.ndarray:
    """
    Compute the 10D geometry view of a graph.

    v0.2: If label_attr is set, the geometry view replaces the 4-path motif
    proxy (dim 10) and assortativity (dim 9) with label-aware features:
      9. Label homophily (fraction of edges with same-label endpoints)
      10. Label diversity (number of distinct labels / n)

    This makes the geometry view label-aware: two graphs with the same topology
    but different label assignments produce different geometry vectors.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if n == 0:
        return np.zeros(10)
    if n == 1:
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    degrees = np.array([d for _, d in G.degree()], dtype=float)
    mean_deg = float(degrees.mean() / max(n - 1, 1))
    std_deg = float(degrees.std() / max(n - 1, 1))
    max_deg = float(degrees.max() / max(n - 1, 1))

    try:
        clustering = float(nx.average_clustering(G))
    except Exception:
        clustering = 0.0

    # Triangle count
    try:
        triangles = sum(nx.triangles(G).values()) // 3
        # Normalize by max possible triangles
        max_triangles = n * (n - 1) * (n - 2) / 6
        tri_norm = float(triangles / max(max_triangles, 1))
    except Exception:
        tri_norm = 0.0

    # Path metrics
    try:
        if nx.is_connected(G):
            mean_path = float(nx.average_shortest_path_length(G))
            diameter = float(nx.diameter(G))
        else:
            # Use largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            sub = G.subgraph(largest_cc)
            mean_path = float(nx.average_shortest_path_length(sub))
            diameter = float(nx.diameter(sub))
    except Exception:
        mean_path = 0.0
        diameter = 0.0

    # Normalize path metrics by n
    mean_path_norm = mean_path / max(n, 1)
    diameter_norm = diameter / max(n, 1)

    # Density
    density = float(nx.density(G))

    # v0.2: Label-aware geometry features (replace assortativity + motif proxy)
    if label_attr is not None:
        # Label homophily: fraction of edges with same-label endpoints
        same_label_edges = 0
        total_edges = 0
        for u, v in G.edges():
            label_u = G.nodes[u].get(label_attr)
            label_v = G.nodes[v].get(label_attr)
            total_edges += 1
            if str(label_u) == str(label_v):
                same_label_edges += 1
        label_homophily = float(same_label_edges / max(total_edges, 1))

        # Label diversity: number of distinct labels / n
        labels = set()
        for node in G.nodes():
            label = G.nodes[node].get(label_attr)
            labels.add(str(label) if label is not None else "__unlabeled__")
        label_diversity = float(len(labels) / max(n, 1))

        assort = label_homophily  # dim 9: label homophily
        motif_norm = label_diversity  # dim 10: label diversity
    else:
        # Topology-only mode (backward compatible with v0.1)
        # Assortativity
        try:
            assort = float(nx.degree_assortativity_coefficient(G))
            if not np.isfinite(assort):
                assort = 0.0
        except Exception:
            assort = 0.0

        # 4-path motif count proxy
        try:
            A = nx.to_numpy_array(G, nodelist=sorted(G.nodes()), dtype=float)
            if A.shape[0] <= 500:
                A4 = np.linalg.matrix_power(A, 4)
                motif_count = float(np.trace(A4))
                motif_norm = motif_count / max(n * (n - 1) * (n - 2) * (n - 3), 1)
            else:
                motif_norm = float(np.mean(degrees ** 2) / max(n, 1))
        except Exception:
            motif_norm = 0.0

    result = np.array([
        mean_deg, std_deg, max_deg, clustering, tri_norm,
        mean_path_norm, diameter_norm, density, assort, motif_norm
    ])
    # Replace any NaN/inf with 0
    result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
    return result


def geometry_quality(geom_vec: np.ndarray) -> float:
    """
    Quality score for geometry view: high when graph has rich combinatorial structure.
    """
    clustering = geom_vec[3]
    tri = geom_vec[4]
    std_deg = geom_vec[1]
    q = (1.0 - np.exp(-clustering * 4.0)) * 0.4 + \
        (1.0 - np.exp(-tri * 50.0)) * 0.3 + \
        (1.0 - np.exp(-std_deg * 4.0)) * 0.3
    return float(np.clip(q, 0.0, 1.0))

"""
TopHash v3 — Persistence View (20D)

Computes persistent homology features of a graph and aggregates them
into a fixed 20-dimensional vector. We use ripser for fast Vietoris-Rips
persistence computation over the shortest-path metric of the graph.

Output dimensions (20):
  H0 persistence (10 dims): mean/std/max/min/sum of H0 lifetimes,
                            number of H0 features, entropy, fraction infinite
  H1 persistence (10 dims): mean/std/max/min/sum of H1 lifetimes,
                            number of H1 features, entropy, persistence energy
"""
import numpy as np
import networkx as nx
from scipy.sparse.csgraph import shortest_path
from scipy.sparse import csr_matrix


def compute_persistence_view(G: nx.Graph, max_dim: int = 1) -> np.ndarray:
    """
    Compute the 20-dimensional persistence view of a graph.

    Pipeline:
      1. Compute all-pairs shortest path distances (use n+1 for disconnected).
      2. Run Vietoris-Rips persistence via ripser on the distance matrix.
      3. Aggregate H0 and H1 diagrams into 10D each.
    """
    n = G.number_of_nodes()
    if n == 0:
        return np.zeros(20)

    # Build adjacency matrix
    A = nx.to_numpy_array(G, nodelist=sorted(G.nodes()), dtype=float)
    np.fill_diagonal(A, 0.0)

    # Compute shortest path distances; disconnected pairs get n+1
    if n > 1 and A.sum() > 0:
        from scipy.sparse.csgraph import shortest_path
        D = shortest_path(csr_matrix(A), directed=False, unweighted=False)
        # Replace inf with finite large value (n+1) for ripser
        D = np.where(np.isinf(D), float(n + 1), D)
        D = np.maximum(D, 0)
        # Symmetrize for safety
        D = (D + D.T) / 2.0
    else:
        D = np.zeros((n, n))

    # Compute persistence via ripser (maxdim=1)
    try:
        from ripser import ripser
        result = ripser(D, distance_matrix=True, maxdim=max_dim, thresh=float(n + 2))
        dgms = result['dgms']
    except Exception:
        # Fallback: zero persistence
        dgms = [np.zeros((0, 2)) for _ in range(max_dim + 1)]

    h0 = dgms[0] if len(dgms) > 0 else np.zeros((0, 2))
    h1 = dgms[1] if len(dgms) > 1 else np.zeros((0, 2))

    return np.concatenate([
        _summarize_diagram(h0, dim=0, n=n),
        _summarize_diagram(h1, dim=1, n=n),
    ])


def _summarize_diagram(dgm: np.ndarray, dim: int, n: int) -> np.ndarray:
    """
    Aggregate a persistence diagram into a 10D vector.
    """
    if dgm is None or len(dgm) == 0:
        return np.zeros(10)

    # Filter out infinite deaths (H0's essential class)
    finite_mask = np.isfinite(dgm[:, 1])
    finite = dgm[finite_mask]
    infinite_count = int((~finite_mask).sum())

    if len(finite) == 0:
        # Only infinite component
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0,
                         float(infinite_count), 0.0, 0.0, float(infinite_count), 0.0])

    births = finite[:, 0]
    deaths = finite[:, 1]
    lifetimes = deaths - births

    # Standard stats on lifetimes
    mean_l = float(np.mean(lifetimes))
    std_l = float(np.std(lifetimes))
    max_l = float(np.max(lifetimes))
    min_l = float(np.min(lifetimes))
    sum_l = float(np.sum(lifetimes))
    n_feat = float(len(lifetimes))

    # Persistence entropy (Shannon over normalized lifetimes)
    if sum_l > 0:
        p = lifetimes / sum_l
        p = p[p > 0]
        entropy = float(-np.sum(p * np.log(p)))
    else:
        entropy = 0.0

    # Fraction of total features (vs node count)
    frac = n_feat / max(n, 1)

    # Persistence energy (sum of squared lifetimes, normalized)
    energy = float(np.sum(lifetimes ** 2)) / max(n, 1)

    return np.array([
        mean_l, std_l, max_l, min_l, sum_l,
        n_feat, entropy, frac, float(infinite_count), energy
    ])


def persistence_quality(dgm_vec: np.ndarray) -> float:
    """
    Internal quality score for the persistence view.
    Higher = more topological signal.
    """
    # Quality = normalized feature count × entropy × energy
    n_feat = dgm_vec[5]
    entropy = dgm_vec[6]
    energy = dgm_vec[9]
    # Bounded quality in [0, 1]-ish
    q = (1.0 - np.exp(-n_feat / 5.0)) * 0.4 + \
        (1.0 - np.exp(-entropy / 2.0)) * 0.3 + \
        (1.0 - np.exp(-energy / 2.0)) * 0.3
    return float(np.clip(q, 0.0, 1.0))

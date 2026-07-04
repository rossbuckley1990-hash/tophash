"""
TopHash v3 — Spectral View (10D)

Computes spectral features of the graph Laplacian and adjacency matrix.
All features are deterministic and training-free.

Output dimensions (10):
  1. Smallest nonzero Laplacian eigenvalue (algebraic connectivity / Fiedler value)
  2. Second smallest nonzero Laplacian eigenvalue (spectral gap)
  3. Largest Laplacian eigenvalue
  4. Mean Laplacian eigenvalue
  5. Std Laplacian eigenvalue
  6. Largest adjacency eigenvalue (spectral radius)
  7. Second largest adjacency eigenvalue
  8. Smallest adjacency eigenvalue
  9. Trace of Laplacian (= 2|E|, normalized by n)
  10. Eigengap: largest gap between consecutive Laplacian eigenvalues (proxy for cluster count)
"""
import numpy as np
import networkx as nx
from scipy.linalg import eigh
from scipy.sparse.linalg import eigsh
from scipy.sparse import csr_matrix


def compute_spectral_view(G: nx.Graph) -> np.ndarray:
    """Compute the 10D spectral view of a graph."""
    n = G.number_of_nodes()
    if n == 0:
        return np.zeros(10)
    if n == 1:
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    A = nx.to_numpy_array(G, nodelist=sorted(G.nodes()), dtype=float)
    np.fill_diagonal(A, 0.0)

    # Laplacian: L = D - A
    D = np.diag(A.sum(axis=1))
    L = D - A

    # Compute eigenvalues (dense for small, sparse for large)
    try:
        if n <= 200:
            eig_L = eigh(L, eigvals_only=True)
            eig_A = eigh(A, eigvals_only=True)
        else:
            k = min(10, n - 1)
            eig_L = eigsh(csr_matrix(L), k=k, which='SM', return_eigenvectors=False)
            eig_L = np.sort(eig_L)
            eig_A = eigsh(csr_matrix(A), k=k, which='LM', return_eigenvectors=False)
            eig_A = np.sort(eig_A)[::-1]
    except Exception:
        return np.zeros(10)

    # Filter near-zero eigenvalues (numerical noise)
    tol = 1e-6
    nonzero_L = eig_L[np.abs(eig_L) > tol]

    if len(nonzero_L) >= 2:
        fiedler = float(nonzero_L[0])
        second = float(nonzero_L[1])
    elif len(nonzero_L) == 1:
        fiedler = float(nonzero_L[0])
        second = 0.0
    else:
        fiedler = 0.0
        second = 0.0

    largest_L = float(eig_L[-1])
    mean_L = float(np.mean(eig_L))
    std_L = float(np.std(eig_L))
    trace_L = float(np.sum(eig_L)) / n  # normalized

    # Adjacency eigenvalues
    if len(eig_A) >= 2:
        spec_radius = float(eig_A[-1])
        second_A = float(eig_A[-2])
    elif len(eig_A) == 1:
        spec_radius = float(eig_A[-1])
        second_A = 0.0
    else:
        spec_radius = 0.0
        second_A = 0.0
    min_A = float(eig_A[0]) if len(eig_A) > 0 else 0.0

    # Eigengap: largest gap between consecutive Laplacian eigenvalues
    if len(eig_L) > 1:
        gaps = np.diff(np.sort(eig_L))
        eigengap = float(np.max(gaps)) if len(gaps) > 0 else 0.0
    else:
        eigengap = 0.0

    return np.array([
        fiedler, second, largest_L, mean_L, std_L,
        spec_radius, second_A, min_A, trace_L, eigengap
    ])


def spectral_quality(spec_vec: np.ndarray) -> float:
    """
    Quality score for spectral view: high when there's real spectral signal
    (non-trivial Fiedler value, distinct eigenvalue structure).
    """
    fiedler = spec_vec[0]
    eigengap = spec_vec[9]
    std_L = spec_vec[4]
    q = (1.0 - np.exp(-fiedler / 1.0)) * 0.4 + \
        (1.0 - np.exp(-eigengap / 2.0)) * 0.3 + \
        (1.0 - np.exp(-std_L / 2.0)) * 0.3
    return float(np.clip(q, 0.0, 1.0))

"""
TopHash v3 — Core 52D Structural Fingerprint

The full TopHash v3 fingerprint combines:
  - 20D weighted persistence view
  - 10D weighted spectral view
  - 10D weighted geometry view
  - 6D  cross terms
  - 6D  meta features
  ────
  52D total
"""
import numpy as np
import networkx as nx
from typing import Dict, Any, Tuple

from .persistence import compute_persistence_view, persistence_quality
from .spectral import compute_spectral_view, spectral_quality
from .geometry import compute_geometry_view, geometry_quality
from .weighting import (
    compute_weights, apply_weights, compute_cross_terms, compute_meta_features
)


# TopHash v3 schema version (immutable, semver)
SCHEMA_VERSION = "tophash-v3-1.0.0"

# Fixed output dimension
TOPHASH_V3_DIM = 52


def compute(G: nx.Graph, label_attr: str = None) -> np.ndarray:
    """
    Compute the 52-dimensional TopHash v3 fingerprint of graph G.

    Deterministic, training-free. Same input graph always produces same output.

    v0.2: If label_attr is set, the fingerprint is LABEL-AWARE.
    - Persistence view uses label-conditioned filtration (label-perturbed metric)
    - Spectral view uses label-aware weighted Laplacian
    - Geometry view includes label homophily and diversity features
    
    Two graphs with the same topology but different labels produce DIFFERENT
    fingerprints when label_attr is set. With label_attr=None (default), the
    fingerprint is topology-only (backward compatible with v0.1).

    Parameters
    ----------
    G : networkx.Graph
        Simple undirected graph. Self-loops will be ignored.
        Nodes may have a `label_attr` attribute for label-aware mode.
    label_attr : str, optional
        If set, enable label-aware fingerprint computation.
        Default None = topology-only.

    Returns
    -------
    np.ndarray of shape (52,)
    """
    # Validate and normalize input
    G = _normalize_graph(G)
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n == 0:
        return np.zeros(TOPHASH_V3_DIM)

    # Compute the three views (label-aware if label_attr is set)
    v_pers = compute_persistence_view(G, label_attr=label_attr)
    v_spec = compute_spectral_view(G, label_attr=label_attr)
    v_geom = compute_geometry_view(G, label_attr=label_attr)

    # Compute per-view quality scores
    q_pers = persistence_quality(v_pers)
    q_spec = spectral_quality(v_spec)
    q_geom = geometry_quality(v_geom)

    # Self-tuning weights
    w = compute_weights(q_pers, q_spec, q_geom)

    # Apply weights
    v_pers_w, v_spec_w, v_geom_w = apply_weights(v_pers, v_spec, v_geom, w)

    # Cross terms (6D)
    v_cross = compute_cross_terms(v_pers, v_spec, v_geom, w)

    # Meta features (6D)
    n_cc = nx.number_connected_components(G)
    v_meta = compute_meta_features(n, m, n_cc, w, q_pers, q_spec, q_geom)

    # Concatenate into 52D fingerprint
    fingerprint = np.concatenate([v_pers_w, v_spec_w, v_geom_w, v_cross, v_meta])
    assert fingerprint.shape == (TOPHASH_V3_DIM,), \
        f"Expected ({TOPHASH_V3_DIM},), got {fingerprint.shape}"

    return fingerprint


def explain(G: nx.Graph, label_attr: str = None) -> Dict[str, Any]:
    """
    Compute the TopHash v3 fingerprint and return a full explanation dict
    suitable for audit, debugging, and product UX.

    v0.2: If label_attr is set, the explanation records that the fingerprint
    is label-aware and which label attribute was used.

    Returns
    -------
    dict with keys:
      schema_version: str
      label_aware: bool
      label_attr: str (or None)
      n_nodes: int
      n_edges: int
      n_components: int
      views:
        persistence: {vector: (20,), quality: float, weight: float}
        spectral:    {vector: (10,), quality: float, weight: float}
        geometry:    {vector: (10,), quality: float, weight: float}
      cross_terms: (6,)
      meta_features: (6,)
      fingerprint: (52,)
    """
    G = _normalize_graph(G)
    n = G.number_of_nodes()
    m = G.number_of_edges()
    n_cc = nx.number_connected_components(G)

    v_pers = compute_persistence_view(G, label_attr=label_attr)
    v_spec = compute_spectral_view(G, label_attr=label_attr)
    v_geom = compute_geometry_view(G, label_attr=label_attr)

    q_pers = persistence_quality(v_pers)
    q_spec = spectral_quality(v_spec)
    q_geom = geometry_quality(v_geom)

    w = compute_weights(q_pers, q_spec, q_geom)
    v_pers_w, v_spec_w, v_geom_w = apply_weights(v_pers, v_spec, v_geom, w)
    v_cross = compute_cross_terms(v_pers, v_spec, v_geom, w)
    v_meta = compute_meta_features(n, m, n_cc, w, q_pers, q_spec, q_geom)
    fingerprint = np.concatenate([v_pers_w, v_spec_w, v_geom_w, v_cross, v_meta])

    return {
        "schema_version": SCHEMA_VERSION,
        "label_aware": label_attr is not None,
        "label_attr": label_attr,
        "n_nodes": n,
        "n_edges": m,
        "n_components": n_cc,
        "views": {
            "persistence": {"vector": v_pers, "weighted_vector": v_pers_w,
                            "quality": q_pers, "weight": w[0]},
            "spectral":    {"vector": v_spec, "weighted_vector": v_spec_w,
                            "quality": q_spec, "weight": w[1]},
            "geometry":    {"vector": v_geom, "weighted_vector": v_geom_w,
                            "quality": q_geom, "weight": w[2]},
        },
        "cross_terms": v_cross,
        "meta_features": v_meta,
        "fingerprint": fingerprint,
    }


def _normalize_graph(G: nx.Graph) -> nx.Graph:
    """
    Normalize input graph: convert to undirected simple graph with consecutive
    integer node labels, no self-loops, no multi-edges.
    """
    if G.is_directed():
        G = G.to_undirected()
    G = nx.Graph(G)  # ensures no multi-edges
    G.remove_edges_from(nx.selfloop_edges(G))
    # Relabel to 0..n-1 for deterministic ordering
    G = nx.convert_node_labels_to_integers(G, first_label=0)
    return G

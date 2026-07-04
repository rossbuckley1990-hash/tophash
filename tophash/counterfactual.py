"""
TopHash Ω∞ — Counterfactual Structural Intelligence

Three-stage engine:
  1. Perturbation algebra — generate admissible edits (deletion, rewiring, etc.)
  2. Response tensor — measure per-view deltas across perturbation type × scale
  3. Invariant core / fragility shell + minimal-edit certificate

The output is not a vector — it is a structured dossier of:
  - invariant core (stable channels)
  - fragility shell (sensitive channels)
  - critical edit map (least-cost regime-flip edits)
"""
import numpy as np
import networkx as nx
import copy
from typing import Dict, Any, List, Tuple, Callable

from . import core as v3_core
from .persistence import compute_persistence_view
from .spectral import compute_spectral_view
from .geometry import compute_geometry_view


PERTURBATION_FAMILIES = [
    "node_deletion",
    "edge_deletion",
    "edge_insertion",
    "rewiring",
    "motif_mask",
]


# ============================================================
# Stage 1 — Perturbation algebra
# ============================================================
def perturb_node_deletion(G: nx.Graph, scale: float) -> nx.Graph:
    """Delete fraction `scale` of nodes uniformly at random (deterministic seed)."""
    rng = np.random.RandomState(hash((scale,)) % (2**32))
    n = G.number_of_nodes()
    k = max(1, int(round(n * scale)))
    nodes_to_remove = rng.choice(list(G.nodes()), size=min(k, n - 1), replace=False)
    H = G.copy()
    H.remove_nodes_from(nodes_to_remove)
    return H


def perturb_edge_deletion(G: nx.Graph, scale: float) -> nx.Graph:
    """Delete fraction `scale` of edges uniformly at random."""
    rng = np.random.RandomState(hash(("edge_del", scale)) % (2**32))
    m = G.number_of_edges()
    k = max(1, int(round(m * scale)))
    edges = list(G.edges())
    if len(edges) == 0:
        return G.copy()
    edges_to_remove = rng.choice(len(edges), size=min(k, len(edges) - 1), replace=False)
    H = G.copy()
    for idx in edges_to_remove:
        u, v = edges[idx]
        if H.has_edge(u, v):
            H.remove_edge(u, v)
    return H


def perturb_edge_insertion(G: nx.Graph, scale: float) -> nx.Graph:
    """Insert fraction `scale` * |non_edges| new edges."""
    rng = np.random.RandomState(hash(("edge_ins", scale)) % (2**32))
    n = G.number_of_nodes()
    nodes = list(G.nodes())
    non_edges = [(u, v) for u in nodes for v in nodes if u < v and not G.has_edge(u, v)]
    k = max(1, int(round(len(non_edges) * scale)))
    if len(non_edges) == 0:
        return G.copy()
    edges_to_add = rng.choice(len(non_edges), size=min(k, len(non_edges)), replace=False)
    H = G.copy()
    for idx in edges_to_add:
        u, v = non_edges[idx]
        H.add_edge(u, v)
    return H


def perturb_rewiring(G: nx.Graph, scale: float) -> nx.Graph:
    """Rewire fraction `scale` of edges: delete an edge and add a random new one."""
    rng = np.random.RandomState(hash(("rewire", scale)) % (2**32))
    edges = list(G.edges())
    k = max(1, int(round(len(edges) * scale)))
    H = G.copy()
    nodes = list(H.nodes())
    for _ in range(k):
        if len(edges) == 0:
            break
        idx = rng.randint(len(edges))
        u, v = edges[idx]
        if H.has_edge(u, v):
            H.remove_edge(u, v)
        # Add a new random edge
        if len(nodes) >= 2:
            i, j = rng.choice(len(nodes), size=2, replace=False)
            H.add_edge(nodes[i], nodes[j])
    return H


def perturb_motif_mask(G: nx.Graph, scale: float) -> nx.Graph:
    """Mask triangles: remove one edge from `scale` fraction of triangles."""
    rng = np.random.RandomState(hash(("motif", scale)) % (2**32))
    triangles = []
    for c in nx.enumerate_all_cliques(G):
        if len(c) == 3:
            triangles.append(tuple(c))
        elif len(c) > 3:
            break
    k = max(1, int(round(len(triangles) * scale)))
    if len(triangles) == 0:
        return G.copy()
    H = G.copy()
    selected = rng.choice(len(triangles), size=min(k, len(triangles)), replace=False)
    for idx in selected:
        a, b, c = triangles[idx]
        # Remove one edge from this triangle (the first that still exists)
        for u, v in [(a, b), (b, c), (a, c)]:
            if H.has_edge(u, v):
                H.remove_edge(u, v)
                break
    return H


PERTURBERS = {
    "node_deletion": perturb_node_deletion,
    "edge_deletion": perturb_edge_deletion,
    "edge_insertion": perturb_edge_insertion,
    "rewiring": perturb_rewiring,
    "motif_mask": perturb_motif_mask,
}


# ============================================================
# Stage 2 — Response tensor
# ============================================================
def compute_response_tensor(G: nx.Graph,
                            scales: List[float] = None,
                            perturbations: List[str] = None) -> Dict[str, Any]:
    """
    Compute the response tensor R[v, π, s] = d_v(F_v(G), F_v(π_s(G))).

    Returns:
      dict with:
        base_fingerprint: (52,)
        base_views: {persistence, spectral, geometry}
        responses: dict[(view, perturbation, scale)] -> delta value
        response_tensor: np.ndarray of shape (3, |π|, |s|)
        perturbations: list of perturbation names
        scales: list of scales
        views: list of view names
    """
    if scales is None:
        scales = [0.05, 0.10, 0.20]
    if perturbations is None:
        perturbations = PERTURBATION_FAMILIES

    G = v3_core._normalize_graph(G)

    # Base views
    f_pers = compute_persistence_view(G)
    f_spec = compute_spectral_view(G)
    f_geom = compute_geometry_view(G)
    base_views = {"persistence": f_pers, "spectral": f_spec, "geometry": f_geom}
    base_fingerprint = v3_core.compute(G)

    # Response tensor
    n_views = 3
    n_perts = len(perturbations)
    n_scales = len(scales)
    tensor = np.zeros((n_views, n_perts, n_scales))

    view_names = ["persistence", "spectral", "geometry"]
    view_funcs = [compute_persistence_view, compute_spectral_view, compute_geometry_view]

    responses = {}

    for pi_idx, pi in enumerate(perturbations):
        perturber = PERTURBERS[pi]
        for s_idx, s in enumerate(scales):
            try:
                G_pert = perturber(G, s)
                f_pert_pers = view_funcs[0](G_pert)
                f_pert_spec = view_funcs[1](G_pert)
                f_pert_geom = view_funcs[2](G_pert)

                # Compute delta: L2 distance per view
                d_pers = float(np.linalg.norm(f_pers - f_pert_pers))
                d_spec = float(np.linalg.norm(f_spec - f_pert_spec))
                d_geom = float(np.linalg.norm(f_geom - f_pert_geom))

                tensor[0, pi_idx, s_idx] = d_pers
                tensor[1, pi_idx, s_idx] = d_spec
                tensor[2, pi_idx, s_idx] = d_geom

                responses[(view_names[0], pi, s)] = d_pers
                responses[(view_names[1], pi, s)] = d_spec
                responses[(view_names[2], pi, s)] = d_geom
            except Exception as e:
                tensor[:, pi_idx, s_idx] = -1.0  # sentinel for failure
                for v_idx, vn in enumerate(view_names):
                    responses[(vn, pi, s)] = -1.0

    return {
        "base_fingerprint": base_fingerprint,
        "base_views": base_views,
        "response_tensor": tensor,
        "responses": responses,
        "perturbations": perturbations,
        "scales": scales,
        "views": view_names,
    }


# ============================================================
# Stage 3 — Invariant core / fragility shell
# ============================================================
def extract_invariant_core(response: Dict[str, Any],
                            inv_threshold: float = 0.1,
                            frag_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Decompose channels into invariant core (low response) and fragility shell (high response).

    A channel is a (view, perturbation) pair. We aggregate across scales using mean.

    Returns:
      dict with invariant_core (stable channels), fragility_shell (sensitive channels),
      and a per-channel invariance score in [0,1] (1 = invariant).
    """
    tensor = response["response_tensor"]
    views = response["views"]
    perturbations = response["perturbations"]
    scales = response["scales"]

    # Aggregate across scales: take max response (worst-case)
    max_response = tensor.max(axis=2)  # shape (n_views, n_perts)

    # Normalize by max in tensor to make threshold interpretable
    norm_factor = max_response.max() if max_response.max() > 0 else 1.0
    norm_response = max_response / norm_factor

    # Invariance score = 1 - normalized response
    invariance = 1.0 - norm_response  # shape (n_views, n_perts)

    invariant_core = []
    fragility_shell = []
    channel_scores = {}

    for v_idx, v in enumerate(views):
        for p_idx, p in enumerate(perturbations):
            score = float(invariance[v_idx, p_idx])
            channel_scores[(v, p)] = score
            if score >= (1.0 - inv_threshold):
                invariant_core.append({"view": v, "perturbation": p, "invariance_score": score})
            elif score <= (1.0 - frag_threshold):
                fragility_shell.append({"view": v, "perturbation": p, "invariance_score": score,
                                        "max_response": float(max_response[v_idx, p_idx])})

    return {
        "invariant_core": invariant_core,
        "fragility_shell": fragility_shell,
        "channel_scores": channel_scores,
        "invariance_threshold": inv_threshold,
        "fragility_threshold": frag_threshold,
    }


# ============================================================
# Stage 4 — Minimal-edit certificate
# ============================================================
def minimal_edit_certificate(G: nx.Graph,
                              target_predicate: Callable[[nx.Graph], bool] = None,
                              max_cost: float = 0.3) -> Dict[str, Any]:
    """
    Find the least-cost admissible edit that flips a target predicate.

    If target_predicate is None, defaults to "graph becomes disconnected".

    Searches over perturbation families and increasing scales, returns the
    first admissible edit set that flips the predicate.
    """
    G = v3_core._normalize_graph(G)

    if target_predicate is None:
        def target_predicate(g):
            return not nx.is_connected(g)

    initial_state = target_predicate(G)
    scales = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30]

    for pi in PERTURBATION_FAMILIES:
        perturber = PERTURBERS[pi]
        for s in scales:
            if s > max_cost:
                break
            try:
                G_pert = perturber(G, s)
                new_state = target_predicate(G_pert)
                if new_state != initial_state:
                    return {
                        "found": True,
                        "perturbation": pi,
                        "scale": s,
                        "cost": s,  # cost = scale for now
                        "initial_predicate_state": initial_state,
                        "flipped_predicate_state": new_state,
                        "perturbed_graph_n_nodes": G_pert.number_of_nodes(),
                        "perturbed_graph_n_edges": G_pert.number_of_edges(),
                        "proof_trail": f"Applied {pi} at scale {s}; predicate flipped from {initial_state} to {new_state}",
                    }
            except Exception:
                continue

    return {"found": False, "searched": list(PERTURBATION_FAMILIES), "scales_searched": scales}


# ============================================================
# Top-level TopHash Ω∞ API
# ============================================================
def tophash_omega(G: nx.Graph,
                  scales: List[float] = None,
                  perturbations: List[str] = None,
                  target_predicate: Callable = None) -> Dict[str, Any]:
    """
    Full TopHash Ω∞ pipeline: perturbation sweep + response tensor +
    invariant core extraction + minimal-edit certificate search.

    Returns a structured dossier.
    """
    G = v3_core._normalize_graph(G)

    response = compute_response_tensor(G, scales=scales, perturbations=perturbations)
    decomposition = extract_invariant_core(response)
    certificate = minimal_edit_certificate(G, target_predicate=target_predicate)

    return {
        "schema_version": "tophash-omega-1.0.0",
        "input_graph": {
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "n_components": nx.number_connected_components(G),
        },
        "base_fingerprint": response["base_fingerprint"],
        "response_tensor_shape": response["response_tensor"].shape,
        "invariant_core": decomposition["invariant_core"],
        "fragility_shell": decomposition["fragility_shell"],
        "channel_scores": {f"{k[0]}|{k[1]}": v for k, v in decomposition["channel_scores"].items()},
        "minimal_edit_certificate": certificate,
        "perturbations": response["perturbations"],
        "scales": response["scales"],
    }

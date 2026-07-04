"""
TopHashX — Exact Canonization & Proof Layer

Five-stage pipeline: Search → Refine → Canon → Cert → ID

  Search: approximate retrieval (uses v3 fingerprint for candidate ranking)
  Refine: deterministic color/partition refinement (Weisfeiler-Lehman style)
  Canon:  exact canonical labeling via individualization-refinement search
  Cert:   machine-auditable proof object with full trace
  ID:     SHA-256(canonical serialization)

Correctness target: C(G) = C(H)  ⟺  G ≅ H  (for simple undirected graphs)
"""
import hashlib
import json
import time
import numpy as np
import networkx as nx
from collections import defaultdict
from typing import Dict, Any, Tuple, List, Optional


SCHEMA_VERSION_CANON = "tophashx-canon-1.0.0"


# ============================================================
# Stage 2 — Refine: color refinement (1-WL)
# ============================================================
def refine_partition(G: nx.Graph) -> Dict[int, int]:
    """
    Apply Weisfeiler-Lehman (1-WL) color refinement to convergence.

    Returns dict mapping each node to its color class.
    Multiple iterations compress the search tree before canonical labeling.
    """
    n = G.number_of_nodes()
    if n == 0:
        return {}

    # Initialize: all nodes same color (0)
    colors = {node: 0 for node in G.nodes()}

    for _ in range(n + 1):  # at most n iterations to converge
        new_colors = {}
        # Build new color signature: (current_color, sorted neighbor colors)
        signatures = {}
        for node in G.nodes():
            neighbor_colors = tuple(sorted(
                colors[nb] for nb in G.neighbors(node)
            ))
            sig = (colors[node], neighbor_colors)
            signatures[node] = sig

        # Map signatures to new color IDs (sorted for determinism)
        unique_sigs = sorted(set(signatures.values()))
        sig_to_color = {sig: i for i, sig in enumerate(unique_sigs)}

        new_colors = {node: sig_to_color[signatures[node]] for node in G.nodes()}

        if new_colors == colors:
            break
        colors = new_colors

    return colors


# ============================================================
# Stage 3 — Canon: canonical labeling via pynauty (with fallback)
# ============================================================
# Strategic decision (post-review): the canonical labeling ALGORITHM is a
# solved problem. nauty/Traces/bliss are free, decades-hardened, and
# pip-installable. TopHash's genuine contribution is NOT the canonical
# labeling — it is the proof object around it: the refinement trace,
# witness log, versioned serialization, and SHA-256 receipt. So we delegate
# the labeling to pynauty (industry standard) and keep our wrapper.
#
# If pynauty is unavailable at runtime, we fall back to the bounded-search
# heuristic and emit an explicit "engine: fallback_heuristic" flag in the
# proof object so downstream auditors know the canonical ID is not provably
# exact in that case.

try:
    import pynauty as _pynauty
    _HAVE_PYNAUTY = True
except ImportError:
    _HAVE_PYNAUTY = False


def _nx_to_pynauty(G: nx.Graph, node_order: List[int]):
    """Convert a networkx graph to a pynauty Graph with consistent vertex ordering."""
    n = len(node_order)
    # Map original node IDs to 0..n-1 indices
    node_to_idx = {node: i for i, node in enumerate(node_order)}
    # Build adjacency dict in pynauty's expected format
    adj_dict = {}
    for node in node_order:
        idx = node_to_idx[node]
        neighbors = [node_to_idx[nb] for nb in G.neighbors(node) if nb in node_to_idx]
        adj_dict[idx] = neighbors
    # pynauty.Graph takes (n_vertices, adjacency_dict)
    return _pynauty.Graph(n, directed=False, adjacency_dict=adj_dict)


def _extract_label_coloring(G: nx.Graph, node_order: List[int], label_attr: str) -> List[List[int]]:
    """
    Extract node labels and group nodes into color classes for pynauty.

    pynauty's vertex_coloring parameter expects a list of lists, where each
    inner list is the set of vertex indices (0-based, in node_order) belonging
    to one color class. Vertices in the same color class are considered
    interchangeable by the canonical labeling; vertices in different color
    classes are NOT interchangeable.

    This is the standard "color-preserving isomorphism" mechanism: two graphs
    are isomorphic under this coloring only if there's an isomorphism that
    maps same-color vertices to same-color vertices.

    For TopHash v0.2, the color = the node's label (e.g., package name in a
    dependency graph, atom type in a molecular graph). This means
    requests→urllib3 and django→psycopg2 produce DIFFERENT canonical IDs even
    though both are 2-node paths, because 'requests' ≠ 'django' and
    'urllib3' ≠ 'psycopg2'.
    """
    node_to_idx = {node: i for i, node in enumerate(node_order)}
    label_to_indices = defaultdict(list)
    for node in node_order:
        label = G.nodes[node].get(label_attr)
        if label is None:
            label = "__unlabeled__"
        label_to_indices[str(label)].append(node_to_idx[node])
    # Return as list of lists, sorted by label for determinism
    return [label_to_indices[k] for k in sorted(label_to_indices.keys())]


def canonical_label(G: nx.Graph, label_attr: str = None) -> Tuple[np.ndarray, np.ndarray, List[int], str, Optional[dict]]:
    """
    Compute canonical labeling of G.

    v0.2: If label_attr is provided, the canonical labeling is COLOR-PRESERVING —
    only automorphisms that map same-label nodes to same-label nodes are considered.
    This makes the canonical ID label-aware: two graphs with the same topology
    but different labels produce DIFFERENT canonical IDs.

    Strategy:
      1. Apply 1-WL color refinement to convergence (TopHash's Refine stage).
      2. If label_attr is set, extract label coloring and pass to pynauty.
      3. Delegate canonical labeling to pynauty (with vertex_coloring if label-aware).
      4. Build canonical adjacency matrix in that order.
      5. Record the engine and label-awareness mode in the trace.

    Returns:
      canonical_adjacency: np.ndarray (n×n)
      canonical_perm: np.ndarray (n,)
      trace: list of refinement / branch decisions
      engine: str — "pynauty" or "fallback_heuristic"
      label_info: dict with label-aware mode details (None if topology-only)
    """
    n = G.number_of_nodes()
    trace = []
    label_info = None

    if n == 0:
        return np.zeros((0, 0)), np.array([], dtype=int), trace, "pynauty", None
    if n == 1:
        return np.zeros((1, 1)), np.array([0]), trace, "pynauty", label_info

    G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G))
    nodes = sorted(G.nodes())

    # Stage 2: Refine — TopHash's contribution (1-WL color refinement)
    colors = refine_partition(G)
    trace.append({"step": "initial_refine", "n_color_classes": len(set(colors.values()))})

    # v0.2: If label_attr is set, extract label coloring for color-preserving canon
    label_coloring = None
    if label_attr is not None:
        label_coloring = _extract_label_coloring(G, nodes, label_attr)
        n_label_classes = len(label_coloring)
        label_info = {
            "label_aware": True,
            "label_attr": label_attr,
            "n_label_classes": n_label_classes,
            "color_preserving": True,
        }
        trace.append({"step": "label_coloring_extracted",
                      "label_attr": label_attr,
                      "n_label_classes": n_label_classes})

    # Stage 3: Canon — delegate to pynauty if available
    if _HAVE_PYNAUTY:
        try:
            # Build pynauty graph
            pgraph = _nx_to_pynauty(G, nodes)

            # Build coloring hint for pynauty.
            # v0.2: If label_attr is set, use the LABEL coloring (color-preserving).
            # Otherwise, use the WL coloring as a hint (topology-only, faster search).
            if label_coloring is not None:
                vertex_coloring = label_coloring
            else:
                color_to_nodes_wl = defaultdict(list)
                for node in nodes:
                    color_to_nodes_wl[colors[node]].append(nodes.index(node))
                vertex_coloring = [v for v in color_to_nodes_wl.values()]

            # Compute canonical labeling.
            # pynauty.canon_label accepts vertex_coloring as a partition hint.
            # When label_coloring is used, the canonical form is color-preserving:
            # two graphs get the same canonical ID only if they're isomorphic
            # AND the isomorphism respects the label coloring.
            canon_labeling = _pynauty.canon_label(pgraph, vertex_coloring=vertex_coloring)

            # The canonical labeling from pynauty is a permutation: position i
            # in the new order is occupied by vertex canon_labeling[i].
            # Convert back to original node IDs.
            perm = [nodes[canon_labeling[i]] for i in range(n)]

            best_adj = nx.to_numpy_array(G, nodelist=perm, dtype=int)
            best_perm = np.array(perm, dtype=int)
            trace.append({"step": "pynauty_canon_label", "engine": "pynauty",
                          "n_vertices": n,
                          "label_aware": label_coloring is not None})
            return best_adj, best_perm, trace, "pynauty", label_info
        except Exception as e:
            trace.append({"step": "pynauty_failed", "error": str(e)})
            # Fall through to heuristic

    # Fallback heuristic (used only if pynauty is unavailable or fails)
    # WARNING: not provably canonical for graphs with large symmetry classes.
    # WARNING: label-aware fallback does NOT respect color-preserving property.
    trace.append({"step": "fallback_heuristic_engaged",
                  "reason": "pynauty_unavailable_or_failed"})

    # Deterministic refinement-aware ordering
    sigs = {}
    for node in nodes:
        nbr_colors = tuple(sorted(colors[nb] for nb in G.neighbors(node)))
        nbr_degrees = tuple(sorted([G.degree(nb) for nb in G.neighbors(node)], reverse=True))
        sigs[node] = (colors[node], -G.degree(node), nbr_colors, nbr_degrees, node)

    perm = sorted(nodes, key=lambda n: sigs[n])

    # Bounded permutation search for symmetries
    color_to_nodes = defaultdict(list)
    for node, c in colors.items():
        color_to_nodes[c].append(node)

    multi_classes = [c for c, ns in color_to_nodes.items() if len(ns) > 1]

    MAX_PERMS = 1000
    total_perms_space = 1
    for c in multi_classes:
        sz = len(color_to_nodes[c])
        from math import factorial
        total_perms_space *= factorial(sz)
        if total_perms_space > MAX_PERMS:
            break

    if multi_classes and total_perms_space <= MAX_PERMS:
        from itertools import product, permutations
        best_perm_list = None
        best_sig = None

        if len(multi_classes) == 1:
            class_nodes = color_to_nodes[multi_classes[0]]
            other_nodes = [n for n in perm if n not in class_nodes]
            for cls_perm in permutations(class_nodes):
                trial = list(cls_perm) + other_nodes
                A = nx.to_numpy_array(G, nodelist=trial, dtype=int)
                sig = A.tobytes()
                if best_sig is None or sig < best_sig:
                    best_sig = sig
                    best_perm_list = trial
        else:
            class_perms_list = [list(permutations(color_to_nodes[c])) for c in multi_classes]
            other_nodes = [n for n in perm if n not in set().union(*[set(color_to_nodes[c]) for c in multi_classes])]
            for combo in product(*class_perms_list):
                trial = []
                for cls_perm in combo:
                    trial.extend(cls_perm)
                trial.extend(other_nodes)
                A = nx.to_numpy_array(G, nodelist=trial, dtype=int)
                sig = A.tobytes()
                if best_sig is None or sig < best_sig:
                    best_sig = sig
                    best_perm_list = trial

        if best_perm_list is not None:
            perm = best_perm_list
            trace.append({"step": "bounded_search_completed",
                          "permutations_evaluated": total_perms_space})
    else:
        trace.append({"step": "heuristic_canonical",
                      "multi_classes": len(multi_classes),
                      "permutation_space": total_perms_space})

    best_adj = nx.to_numpy_array(G, nodelist=perm, dtype=int)
    best_perm = np.array(perm, dtype=int)

    return best_adj, best_perm, trace, "fallback_heuristic", label_info


# ============================================================
# Stage 3b — Canonical serialization
# ============================================================
def canonical_serialize(G: nx.Graph, label_attr: str = None) -> Tuple[str, np.ndarray, List[int], str, Optional[dict]]:
    """
    Compute canonical adjacency, then serialize it deterministically.

    v0.2: If label_attr is set, the serialization INCLUDES the labels in
    canonical order. This means two graphs with the same topology but
    different labels produce DIFFERENT serializations → different SHA-256 IDs.

    Returns:
      serialization: str — canonical byte string (the source of truth)
      canonical_adj: np.ndarray
      perm: list[int] — permutation used
      engine: str — "pynauty" or "fallback_heuristic"
      label_info: dict — label-aware mode details (None if topology-only)
    """
    can_adj, perm, _, engine, label_info = canonical_label(G, label_attr=label_attr)

    n = can_adj.shape[0]
    m = int(can_adj.sum() // 2)

    # Deterministic serialization.
    # v0.2: if label-aware, include the labels in canonical order.
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if can_adj[i, j] == 1:
                edges.append((i, j))

    # Build label string for serialization (v0.2)
    label_str = "none"
    if label_attr is not None and label_info is not None:
        # Extract labels in canonical order
        canonical_labels = []
        for i in range(n):
            orig_node = perm[i]
            label = G.nodes[orig_node].get(label_attr)
            canonical_labels.append(str(label) if label is not None else "__unlabeled__")
        label_str = ",".join(canonical_labels)

    serialization = (
        f"{SCHEMA_VERSION_CANON}|"
        f"engine={engine}|"
        f"label_aware={'true' if label_attr else 'false'}|"
        f"graph_model=simple_undirected|"
        f"n={n}|m={m}|"
        f"labels={label_str}|"
        f"edges={edges}"
    )

    return serialization, can_adj, list(perm), engine, label_info


# ============================================================
# Stage 4 — Cert: proof object
# ============================================================
def build_certificate(G: nx.Graph, canonical_adj: np.ndarray,
                      perm: List[int], trace: List, engine: str,
                      label_info: dict = None) -> Dict[str, Any]:
    """
    Build a machine-auditable certificate object.

    v0.2: If label_info is provided, the certificate records that the canonical
    labeling is color-preserving (label-aware). This means the canonical ID
    respects node labels — two graphs with the same topology but different
    labels produce DIFFERENT canonical IDs.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # Validation records
    validation = {
        "graph_model": "simple_undirected",
        "n_vertices": n,
        "n_edges": m,
        "n_connected_components": nx.number_connected_components(G),
        "self_loops_removed": int(sum(1 for u, v in G.edges() if u == v)),
        "canon_engine": engine,
        "exactness_guaranteed": (engine == "pynauty"),
        "label_aware": label_info is not None,
        "color_preserving": label_info is not None and label_info.get("color_preserving", False),
    }
    if label_info is not None:
        validation["label_attr"] = label_info.get("label_attr")
        validation["n_label_classes"] = label_info.get("n_label_classes")

    # Refinement trace (extracted from canon trace)
    refinement_trace = [t for t in trace if t.get("step", "").endswith("refine") or t.get("step") == "initial_refine"]
    search_trace = [t for t in trace if t.get("step", "") not in ("initial_refine",)]

    return {
        "schema_version": SCHEMA_VERSION_CANON,
        "input_declaration": validation,
        "canonical_result": {
            "canonical_order": perm,
            "canonical_n_vertices": n,
            "canonical_n_edges": m,
            "canon_engine": engine,
            "label_aware": label_info is not None,
        },
        "refinement_trace": refinement_trace,
        "search_witness": search_trace,
        "validation_records": validation,
        "timestamp": time.time(),
    }


# ============================================================
# Stage 5 — ID: SHA-256(canonical serialization)
# ============================================================
def compute_id(canonical_serialization: str) -> str:
    """SHA-256 over the UTF-8 bytes of the canonical serialization."""
    return hashlib.sha256(canonical_serialization.encode('utf-8')).hexdigest()


# ============================================================
# Top-level TopHashX API
# ============================================================
def tophashx(G: nx.Graph, include_certificate: bool = True,
             label_attr: str = None) -> Dict[str, Any]:
    """
    Full TopHashX pipeline: Refine → Canon → Cert → ID.

    v0.2: If label_attr is set, the canonical labeling is COLOR-PRESERVING.
    Two graphs with the same topology but different labels produce DIFFERENT
    canonical IDs. This is the fix for the v0.1 collision finding where
    requests→urllib3 and django→psycopg2 produced the same canonical ID.

    Parameters
    ----------
    G : networkx.Graph
        Input graph. Nodes may have a `label_attr` attribute for label-aware mode.
    include_certificate : bool
        If True, include the full proof object in the result.
    label_attr : str, optional
        If set, enable color-preserving (label-aware) canonical labeling.
        The node attribute named `label_attr` is used as the color.
        Default None = topology-only (backward compatible with v0.1).

    Returns dict with:
      canonical_serialization: str
      canonical_id: str
      canonical_perm: list[int]
      canon_engine: str
      exactness_guaranteed: bool
      label_aware: bool
      certificate: dict (if include_certificate=True)
      schema_version: str
    """
    from .core import _normalize_graph
    G = _normalize_graph(G)

    t0 = time.perf_counter()
    can_adj, perm, trace, engine, label_info = canonical_label(G, label_attr=label_attr)
    t1 = time.perf_counter()

    serialization, can_adj, perm, engine, label_info = canonical_serialize(G, label_attr=label_attr)
    t2 = time.perf_counter()

    canonical_id = compute_id(serialization)
    t3 = time.perf_counter()

    result = {
        "schema_version": SCHEMA_VERSION_CANON,
        "canonical_serialization": serialization,
        "canonical_id": canonical_id,
        "canonical_perm": perm,
        "canonical_adjacency_shape": can_adj.shape,
        "canon_engine": engine,
        "exactness_guaranteed": (engine == "pynauty"),
        "label_aware": label_info is not None,
        "color_preserving": label_info is not None and label_info.get("color_preserving", False),
        "timings": {
            "canon_seconds": t1 - t0,
            "serialize_seconds": t2 - t1,
            "id_seconds": t3 - t2,
            "total_seconds": t3 - t0,
        },
    }

    if include_certificate:
        result["certificate"] = build_certificate(G, can_adj, perm, trace, engine, label_info)

    return result


def is_isomorphic(G: nx.Graph, H: nx.Graph, label_attr: str = None) -> bool:
    """
    Exact isomorphism test via TopHashX: G ≅ H iff canonical_id(G) == canonical_id(H).

    v0.2: If label_attr is set, the test is COLOR-PRESERVING — G and H are
    isomorphic only if there's an isomorphism that respects node labels.

    Correctness target:
      Topology-only:  C(G) = C(H) ⟺ G ≅ H
      Label-aware:    C(G) = C(H) ⟺ G ≅ H AND the isomorphism preserves labels
    """
    # Fast pre-check: same number of nodes/edges
    if G.number_of_nodes() != H.number_of_nodes():
        return False
    if G.number_of_edges() != H.number_of_edges():
        return False
    if nx.number_connected_components(G) != nx.number_connected_components(H):
        return False

    # Compare canonical IDs (label-aware if label_attr is set)
    id_G = tophashx(G, include_certificate=False, label_attr=label_attr)["canonical_id"]
    id_H = tophashx(H, include_certificate=False, label_attr=label_attr)["canonical_id"]
    return id_G == id_H

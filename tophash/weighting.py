"""
TopHash v3 — Self-Tuning Weight Engine

Computes internal quality scores for each view and converts them into
normalized weights. The weighting is deterministic, training-free, and
adapts to which view is most informative for the current graph.
"""
import numpy as np


def compute_weights(q_pers: float, q_spec: float, q_geom: float,
                    eps: float = 1e-6) -> np.ndarray:
    """
    Convert three quality scores in [0,1] into normalized weights summing to 1.

    Uses softmax-like normalization with a temperature that ensures
    no single view dominates unless its quality is genuinely much higher.
    """
    q = np.array([q_pers, q_spec, q_geom])
    # Square-root sharpening: emphasizes differences without over-concentrating
    q_sharp = np.sqrt(np.maximum(q, 0.0))
    total = q_sharp.sum()
    if total < eps:
        # Equal weights fallback
        return np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
    return q_sharp / total


def apply_weights(v_pers: np.ndarray, v_spec: np.ndarray, v_geom: np.ndarray,
                 w: np.ndarray) -> tuple:
    """
    Apply weights to each view vector. Returns (weighted_pers, weighted_spec, weighted_geom).

    Weighting is multiplicative per-view (not per-element).
    """
    return v_pers * w[0], v_spec * w[1], v_geom * w[2]


def compute_cross_terms(v_pers: np.ndarray, v_spec: np.ndarray,
                        v_geom: np.ndarray, w: np.ndarray) -> np.ndarray:
    """
    Compute 6 cross-term features that capture interactions between views.

    Cross terms (views have different dimensions, so we use dimension-independent
    summary statistics rather than raw dot products):
      1. pers_spec_mean_product: mean(pers) * mean(spec) * weight product
      2. pers_geom_mean_product: mean(pers) * mean(geom) * weight product
      3. spec_geom_mean_product: mean(spec) * mean(geom) * weight product
      4. |pers_mean - spec_mean| (signed difference)
      5. |spec_mean - geom_mean|
      6. weight entropy (higher when weights are balanced)
    """
    # Mean of each view (scalar summaries, dimension-independent)
    mean_p = float(np.mean(v_pers))
    mean_s = float(np.mean(v_spec))
    mean_g = float(np.mean(v_geom))

    # Cross products of mean summaries, weighted
    ps_prod = mean_p * mean_s * w[0] * w[1]
    pg_prod = mean_p * mean_g * w[0] * w[2]
    sg_prod = mean_s * mean_g * w[1] * w[2]

    # Mean differences
    diff_ps = mean_p - mean_s
    diff_sg = mean_s - mean_g

    # Weight entropy (normalized to [0, 1])
    w_safe = np.maximum(w, 1e-10)
    entropy = float(-np.sum(w_safe * np.log(w_safe))) / np.log(3)

    return np.array([ps_prod, pg_prod, sg_prod, diff_ps, diff_sg, entropy])


def compute_meta_features(n: int, m: int, n_cc: int,
                          w: np.ndarray, q_pers: float, q_spec: float,
                          q_geom: float) -> np.ndarray:
    """
    Compute 6 meta-features describing the graph and the weighting decision.

    Meta features:
      1. log(n) — size signal
      2. log(m + 1) — edge count signal
      3. log(n_cc) — component count signal
      4. w_pers — persistence weight (record of decision)
      5. w_spec — spectral weight
      6. w_geom — geometry weight
    """
    return np.array([
        float(np.log(max(n, 1))),
        float(np.log(max(m + 1, 1))),
        float(np.log(max(n_cc, 1))),
        float(w[0]),
        float(w[1]),
        float(w[2]),
    ])

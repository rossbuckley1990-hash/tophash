"""
TopHash — The Structural Identity Layer for the AI Era

Public API:
  tophash.v3.compute(G)        -> np.ndarray (52,)
  tophash.v3.explain(G)        -> dict
  tophash.ensemble.compute(G)  -> np.ndarray (156,)
  tophash.ensemble.explain(G)  -> dict
  tophash.canon.tophashx(G)    -> dict (canonical ID + certificate)
  tophash.canon.is_isomorphic(G, H) -> bool
  tophash.omega.tophash_omega(G)    -> dict (counterfactual dossier)

Submodules:
  tophash.core          — v3 fingerprint
  tophash.ensemble      — v3 ensemble (156D)
  tophash.persistence   — persistence view (20D)
  tophash.spectral      — spectral view (10D)
  tophash.geometry      — geometry view (10D)
  tophash.weighting     — self-tuning weight engine
  tophash.canon         — TopHashX (exact canonization + proof)
  tophash.counterfactual — TopHash Ω∞ (perturbation + response + invariant core)
  tophash.distance      — similarity/distance utilities
"""

from . import core as v3_core
from . import ensemble as v3_ensemble
from . import canon as tophashx
from . import counterfactual as omega
from . import distance

# Convenience aliases
v3 = v3_core
ensemble = v3_ensemble
canon = tophashx
omega_module = omega

__version__ = "1.0.0"
__all__ = [
    "v3", "ensemble", "canon", "omega", "distance",
    "TOPHASH_V3_DIM", "TOPHASH_V3E_DIM",
]

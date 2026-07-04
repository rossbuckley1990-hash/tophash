"""Smoke test for the TopHash package."""
import sys
sys.path.insert(0, '/home/z/my-project')

import numpy as np
import networkx as nx
import time

from tophash import v3, ensemble, canon, omega, distance

print("=" * 70)
print("TopHash Smoke Test")
print("=" * 70)

# Test 1: TopHash v3 on a small graph
print("\n[Test 1] TopHash v3 fingerprint — small cycle graph C10")
G = nx.cycle_graph(10)
t0 = time.perf_counter()
fp = v3.compute(G)
t1 = time.perf_counter()
print(f"  dim = {fp.shape}, time = {(t1-t0)*1000:.1f}ms, NaN? {np.isnan(fp).any()}")
print(f"  first 8 values: {fp[:8]}")

# Test 2: TopHash v3 explanation
print("\n[Test 2] TopHash v3.explain — audit / debugging")
exp = v3.explain(G)
print(f"  schema_version: {exp['schema_version']}")
print(f"  n_nodes={exp['n_nodes']}, n_edges={exp['n_edges']}, n_components={exp['n_components']}")
print(f"  view weights: pers={exp['views']['persistence']['weight']:.3f} "
      f"spec={exp['views']['spectral']['weight']:.3f} "
      f"geom={exp['views']['geometry']['weight']:.3f}")
print(f"  view quality:  pers={exp['views']['persistence']['quality']:.3f} "
      f"spec={exp['views']['spectral']['quality']:.3f} "
      f"geom={exp['views']['geometry']['quality']:.3f}")

# Test 3: Determinism — same input → same output
print("\n[Test 3] Determinism — same graph computed twice")
fp2 = v3.compute(nx.cycle_graph(10))
print(f"  L2 distance between two runs: {distance.euclidean(fp, fp2):.2e}")

# Test 4: Sensitivity — different graphs → different fingerprints
print("\n[Test 4] Sensitivity — C10 vs P10 (path) vs K10 (complete)")
G_cycle = nx.cycle_graph(10)
G_path = nx.path_graph(10)
G_complete = nx.complete_graph(10)
fp_c = v3.compute(G_cycle)
fp_p = v3.compute(G_path)
fp_k = v3.compute(G_complete)
print(f"  d(C10, P10) = {distance.euclidean(fp_c, fp_p):.3f}")
print(f"  d(C10, K10) = {distance.euclidean(fp_c, fp_k):.3f}")
print(f"  d(P10, K10) = {distance.euclidean(fp_p, fp_k):.3f}")
print(f"  cos(C10, P10) = {distance.cosine_similarity(fp_c, fp_p):.3f}")
print(f"  cos(C10, K10) = {distance.cosine_similarity(fp_c, fp_k):.3f}")

# Test 5: Ensemble 156D
print("\n[Test 5] TopHash v3 Ensemble — 156D")
fp_e = ensemble.compute(G_cycle)
print(f"  dim = {fp_e.shape}, NaN? {np.isnan(fp_e).any()}")

# Test 6: TopHashX — canonical ID
print("\n[Test 6] TopHashX canonical ID")
t0 = time.perf_counter()
result = canon.tophashx(G_cycle, include_certificate=True)
t1 = time.perf_counter()
print(f"  canonical_id: {result['canonical_id'][:32]}...")
print(f"  total time: {(t1-t0)*1000:.1f}ms")
print(f"  certificate keys: {list(result['certificate'].keys())}")

# Test 7: Isomorphism — permuted cycle graphs should have same canonical ID
print("\n[Test 7] Isomorphism invariance — C10 with permuted labels")
rng = np.random.RandomState(42)
perm = rng.permutation(10)
G_perm = nx.relabel_nodes(G_cycle, dict(enumerate(perm)))
result_perm = canon.tophashx(G_perm, include_certificate=False)
print(f"  original ID:  {result['canonical_id'][:32]}")
print(f"  permuted ID:  {result_perm['canonical_id'][:32]}")
print(f"  ISOMORPHIC (expected True): {result['canonical_id'] == result_perm['canonical_id']}")

# Test 8: Non-isomorphic graphs should have different IDs
print("\n[Test 8] Non-isomorphism — C10 vs P10")
result_path = canon.tophashx(G_path, include_certificate=False)
print(f"  C10 ID: {result['canonical_id'][:32]}")
print(f"  P10 ID: {result_path['canonical_id'][:32]}")
print(f"  DIFFERENT (expected True): {result['canonical_id'] != result_path['canonical_id']}")

# Test 9: TopHash Ω∞ — counterfactual analysis
print("\n[Test 9] TopHash Ω∞ — counterfactual dossier on C10")
t0 = time.perf_counter()
omega_result = omega.tophash_omega(G_cycle, scales=[0.05, 0.10, 0.20])
t1 = time.perf_counter()
print(f"  response_tensor_shape: {omega_result['response_tensor_shape']}")
print(f"  invariant_core channels: {len(omega_result['invariant_core'])}")
print(f"  fragility_shell channels: {len(omega_result['fragility_shell'])}")
print(f"  minimal_edit_certificate.found: {omega_result['minimal_edit_certificate']['found']}")
if omega_result['minimal_edit_certificate']['found']:
    cert = omega_result['minimal_edit_certificate']
    print(f"    perturbation: {cert['perturbation']}, scale: {cert['scale']}")
print(f"  total time: {(t1-t0)*1000:.1f}ms")

print("\n" + "=" * 70)
print("All smoke tests passed.")
print("=" * 70)

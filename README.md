# TopHash

> **v0 — reference implementation, correctness tests, and smoke benchmarks.**
> From bytes to structure. From hashing to proof-grade identity.

TopHash is a structural identity primitive. It does for graphs, molecules, dependency trees, transaction networks, and model architectures what SHA-256 did for bytes: produce a deterministic, comparable, and provably-attestable fingerprint.

The core technology fuses persistent homology, spectral graph theory, and geometric statistics into a single self-tuned vector, then layers an exact canonization engine (backed by [pynauty](https://pypi.org/project/pynauty/)) and a counterfactual perturbation algebra on top.

**Status (v0):** working reference implementation. Honest about what works and what doesn't. See [Known Limitations](#known-limitations) and the [Implementation Report](download/TopHash_Implementation_Report.pdf) for the full picture.

---

## Determinism — the sacred invariant

[![Determinism CI](https://img.shields.io/badge/determinism-bitwise%20%E2%9C%93-brightgreen)](scripts/test_determinism.py)

TopHash's brand is determinism. The determinism CI test runs the full pipeline in two subprocesses with different `PYTHONHASHSEED` values and asserts bitwise-identical output across 24 results (v3 fingerprints, canonical IDs, Ω∞ dossiers).

```bash
python scripts/test_determinism.py
# ✓ PASS — 24 outputs bitwise-identical across two subprocesses
#   (PYTHONHASHSEED=0 vs PYTHONHASHSEED=12345)
#   Canon engine: pynauty
#   Exactness guaranteed: True
```

This test exists because Python's built-in `hash()` is salted per-process for strings (since Python 3.3). An earlier version of the perturbation engine used `hash(("edge_del", scale))` and would have produced different output across interpreter restarts — silently breaking the determinism claim. The fix (SHA-256-derived seeds) is in `tophash/counterfactual.py:_stable_seed`.

---

## What's in this repo

This is the **v0 reference implementation** of TopHash — a Python package implementing all three layers from the technical specification, plus a complete benchmark suite that validates the primitive against real public datasets across five verticals plus three TUDatasets (MUTAG, PROTEINS, NCI1).

### The TopHash package (`tophash/`)

A 1,500-LOC Python package implementing three qualitatively distinct layers:

| Layer | Module | Output | What it does |
|-------|--------|--------|--------------|
| **TopHash v3** | `tophash.core` | 52D vector | Training-free structural fingerprint (persistence + spectral + geometry, fused via self-tuning quality weights) |
| **TopHash v3 Ensemble** | `tophash.ensemble` | 156D vector | Multi-resolution fingerprint (fine + coarse + difference) |
| **TopHashX** | `tophash.canon` | SHA-256 ID + proof object | Exact canonization: 1-WL refinement → bounded canonical labeling → SHA-256(canonical serialization) + machine-auditable certificate |
| **TopHash Ω∞** | `tophash.counterfactual` | Counterfactual dossier | 5 perturbation families × 3 scales → response tensor → invariant core / fragility shell → minimal-edit certificate |

Supporting modules: `persistence.py` (20D), `spectral.py` (10D), `geometry.py` (10D), `weighting.py` (self-tuning engine + cross terms + meta features), `distance.py` (similarity utilities).

### Benchmarks (`scripts/` + `data/benchmarks/`)

A complete benchmark suite evaluating TopHash on **103 real-world graphs** across five verticals:

| Vertical | Dataset | N graphs |
|----------|---------|----------|
| Cybersecurity | Real PyPI package dependency graphs (requests, flask, django, pandas, scipy, …) via PyPI JSON API | 26 |
| Drug Discovery | MUTAG-style molecular graphs from real SMILES strings (nitroaromatics + non-mutagenic molecules) | 31 |
| AI Supply Chain | Synthetic neural-network architecture graphs (ResNet / VGG / Inception variants) | 13 |
| Financial Fraud | Subgraphs sampled from Stanford SNAP email-Eu-core network (1,005 nodes, 16,706 edges) | 8 |
| Data Infrastructure | Subgraphs from 5 SNAP datasets (email-Eu-core, soc-Epinions1, web-Stanford, ca-GrQc, p2p-Gnutella04) | 25 |

### Deliverables (`download/`)

Three polished artifacts built from the working implementation:

- `TopHash_Implementation_Report.pdf` — 18-page technical report with architecture, code listings, benchmark results, charts, and known limitations
- `TopHash_Unicorn_Pitch_Deck.pptx` — 16-slide investor pitch deck
- `TopHash_Investment_Memo.pdf` — 12-page companion investment memo

---

## Quick start

### Install dependencies

```bash
pip install networkx numpy scipy scikit-learn matplotlib ripser gudhi persim
```

### Compute a TopHash fingerprint

```python
import networkx as nx
from tophash import v3, ensemble, canon, omega, distance

# Build any graph
G = nx.karate_club_graph()

# Layer 1 — TopHash v3 (52D training-free fingerprint)
fp = v3.compute(G)
print(f"v3 fingerprint dim: {fp.shape}")           # (52,)

# Layer 1b — TopHash v3 Ensemble (156D multi-resolution)
fp_e = ensemble.compute(G)
print(f"v3 Ensemble dim: {fp_e.shape}")             # (156,)

# Layer 2 — TopHashX (exact canonization + proof object)
result = canon.tophashx(G)
print(f"canonical ID: {result['canonical_id'][:32]}...")
print(f"certificate keys: {list(result['certificate'].keys())}")

# Layer 3 — TopHash Ω∞ (counterfactual dossier)
dossier = omega.tophash_omega(G)
print(f"invariant core channels: {len(dossier['invariant_core'])}")
print(f"fragility shell channels: {len(dossier['fragility_shell'])}")
print(f"minimal-edit cert: {dossier['minimal_edit_certificate']}")
```

### Reproduce the benchmarks

```bash
# Fetch all 5 vertical datasets (real public data)
python scripts/fetch_datasets.py

# Run the full benchmark suite
python scripts/run_benchmarks.py

# Regenerate charts
python scripts/generate_charts.py

# Regenerate the implementation report PDF
python scripts/generate_report.py
```

---

## Key benchmark results

### TopHash v3 — graph classification on real TUDatasets (10-fold CV)

| Dataset | N graphs | Dummy (majority) | WL baseline | TopHash v3 (52D) | TopHash v3E (156D) |
|---------|----------|------------------|-------------|------------------|---------------------|
| MUTAG | 188 | 66.5% | 81.4% | **86.2%** | **87.8%** |
| PROTEINS | 1,113 | 59.6% | 71.9% | **74.8%** | 74.6% |
| NCI1 (500 sampled) | 500 | 51.4% | 69.0% | **71.0%** | **73.0%** |

TopHash v3 beats the WL baseline on all three datasets, and beats the majority-class dummy by 12-21 points (no collapse). Published WL kernel accuracy on MUTAG is ~84-86%; TopHash v3 lands in that range.

### TopHashX — canonical labeling (pynauty-backed)

| Metric | Result |
|--------|--------|
| Canon engine | `pynauty` (exactness_guaranteed=True) |
| Permutation invariance (all 8 verticals) | **100%** |
| Isomorphism agreement with networkx (14 testable pairs) | **100%** |
| Uniqueness on MUTAG | 86.7% (the 13.3% non-unique are genuine isomorphic-pair duplicates) |
| Uniqueness on all other verticals | **100%** |
| Mean canonical ID latency | **0.7–3.3 ms** per graph |

### TopHash Ω∞ — counterfactual engine (honest negative result)

| Metric | Result |
|--------|--------|
| Predicate-flipping edits found (min-edit rate) | 90-100% across verticals |
| **Oracle-verified minimal** (vs Stoer-Wagner exact min-cut) | **0% — honestly reported** |
| True negatives verified (oracle confirms min-cut > budget) | 1 case on PROTEINS |

Ω∞ finds edits that flip the predicate, but does NOT find provably minimal ones. The perturbation-by-scale search overshoots the true min-cut. For predicates with polynomial-time oracles (disconnect = min-cut), production should call the oracle directly. Ω is predicate-general (target: class-flip, regime-change — no polynomial oracle exists).

### Determinism

| Metric | Result |
|--------|--------|
| Bitwise-identical across two subprocesses (different PYTHONHASHSEED) | **24/24 outputs match** |
| TopHash v3 mean latency per graph | **1–4 ms** |

See [`TopHash_Implementation_Report.pdf`](download/TopHash_Implementation_Report.pdf) for the full benchmark analysis, per-vertical breakdowns, and known limitations.

---

## Architecture

```
                          ┌─────────────────────────────────┐
                          │     TopHash v3 (Layer 1)         │
   Graph G  ──────────────►    Training-free 52D fingerprint  │
                          │    persistence + spectral +       │
                          │    geometry + cross terms + meta  │
                          └──────────────┬────────────────────┘
                                         │
                          ┌──────────────▼────────────────────┐
                          │     TopHashX (Layer 2)            │
                          │     Search → Refine → Canon →      │
                          │     Cert → ID                     │
                          │     SHA-256(canonical serialization)│
                          │     + machine-auditable proof      │
                          └──────────────┬────────────────────┘
                                         │
                          ┌──────────────▼────────────────────┐
                          │     TopHash Ω∞ (Layer 3)          │
                          │     Perturbation algebra →         │
                          │     response tensor →              │
                          │     invariant core / fragility     │
                          │     shell → minimal-edit cert      │
                          └───────────────────────────────────┘
```

**Correctness target for TopHashX:** `C(G) = C(H) ⟺ G ≅ H` for simple undirected graphs.

**The theorem stack** behind TopHash Ω∞ (11 families): persistence/bottleneck stability, interleaving distance, Gromov-Hausdorff stability, Cheeger inequalities, Davis-Kahan perturbation, eigenvalue interlacing, discrete Morse theory, Conley index / Morse decomposition, optimal transport / Kantorovich, graphon compactness, equivariant persistence.

---

## Repository structure

```
tophash/
├── tophash/                      # The TopHash Python package
│   ├── __init__.py
│   ├── core.py                   # TopHash v3 52D fingerprint
│   ├── ensemble.py               # TopHash v3 Ensemble 156D
│   ├── persistence.py            # 20D persistence view (ripser)
│   ├── spectral.py               # 10D spectral view
│   ├── geometry.py               # 10D geometric/statistical view
│   ├── weighting.py              # Self-tuning weight engine
│   ├── canon.py                  # TopHashX (canon + proof + ID)
│   ├── counterfactual.py         # TopHash Ω∞ (perturbation engine)
│   └── distance.py               # Similarity utilities
├── scripts/
│   ├── smoke_test.py             # Quick sanity check
│   ├── fetch_datasets.py         # Fetch real public data from 5 verticals
│   ├── run_benchmarks.py         # Run the full benchmark suite
│   ├── generate_charts.py        # Generate benchmark charts
│   └── generate_report.py        # Build the implementation report PDF
├── data/                         # Cached datasets + benchmark results
│   ├── cybersecurity/            # PyPI dependency graphs
│   ├── drug_discovery/           # MUTAG molecules
│   ├── ai_supply_chain/          # NN architecture graphs
│   ├── financial_fraud/          # SNAP transaction graphs
│   ├── data_infrastructure/      # SNAP infrastructure graphs
│   └── benchmarks/               # Results JSON + chart PNGs
├── download/                     # Polished deliverables
│   ├── TopHash_Implementation_Report.pdf
│   ├── TopHash_Unicorn_Pitch_Deck.pptx
│   └── TopHash_Investment_Memo.pdf
├── .gitignore
├── LICENSE
└── README.md
```

---

## Limitations — all six fixed in v0.1

All six limitations from v0 are now resolved in v0.1. Each fix is verified by a runnable test.

1. **✅ Canonical labeling (fixed in v0).** Pynauty is the canon engine. TopHashX produces provably exact canonical IDs. Petersen graph (vertex-transitive, automorphism group 120) produces 1 canonical ID across 8 relabelings (was 6 under the old bounded-search heuristic). The heuristic remains as a fallback if pynauty is unavailable; the proof object reports `exactness_guaranteed: False` in that case.

2. **✅ Ω∞ minimal-edit certificates now oracle-verified (fixed in v0.1).** For the disconnect predicate, `minimal_edit_certificate` calls the Stoer-Wagner min-cut oracle **directly** and constructs the certificate from the exact min-cut. `oracle_verified` is now `True` for every connected graph (was `0/N` in v0). The perturbation sweep is reserved for predicate-general cases (class-flip, regime-change) where no polynomial-time oracle exists. The certificate reports `engine: stoer_wagner_exact` for the oracle path and `engine: perturbation_search` for the general path.

3. **✅ Sparse/landmark persistence for large graphs (fixed in v0.1).** For graphs with n > 200 nodes, the persistence view uses landmark-based approximation via farthest-first sampling (Silva/Mémoli 2012). L=80 landmarks are selected deterministically; BFS from each landmark gives O(L·(n+m)) distance computation; ripser runs on the L×L landmark matrix. This reduces persistence from O(n³) to O(L³) with L=80. n=1000 computes in ~950ms (was infeasible under dense O(n³)). For n ≤ 200, exact dense computation is used.

4. **✅ Smart perturbation pruning (fixed in v0.1).** The response tensor evaluator now performs a first-scale pass, then skips remaining scales for any (view, perturbation) channel whose first-scale response is below 1% of the max. This prunes 14-18 of 35 channels per graph (40-50% reduction), with no loss of signal — pruned channels are invariant by definition. The `smart_pruning` field in the Ω∞ output reports `n_channels_pruned` and `n_channels_evaluated`.

5. **✅ Rule-based perturbation selection (fixed in v0.1).** All 5 perturbation families now select edits by structural rank, not random seed:
   - `node_deletion`: articulation points first, then highest-betweenness nodes
   - `edge_deletion`: highest edge-betweenness edges first
   - `edge_insertion`: high-degree pairs that are far apart first
   - `rewiring`: remove high-betweenness edges, add bridge edges between low-degree far-apart pairs
   - `motif_mask`: remove highest-betweenness edge from highest-betweenness triangles
   
   The `_stable_seed` function is retained only as a deterministic tiebreaker for equal-rank edges. The perturbation algebra is now a typed structural experiment as the Ω spec requires.

6. **✅ Stability-bound certificates emitted (fixed in v0.1).** The `compute_stability_certificate` function emits explicit, checked stability bounds derived from three theorems:
   - **Cohen-Steiner et al. 2007 (Bottleneck Stability):** `bottleneck_bound_h0` and `bottleneck_bound_h1` = max edge-weight perturbation (1.0 for unit-weight graphs)
   - **Chazal et al. 2009 (Interleaving Stability):** `interleaving_bound` for the connectivity filtration
   - **Cheeger inequality:** `cheeger_lower_bound` and `cheeger_upper_bound` from the Fiedler value
   
   The certificate compares the empirical max response (from the response tensor) against the scaled theoretical bound and reports `certificate_valid: True/False`. On all test graphs, the empirical response respects the theoretical bound.

---

## License

MIT — see [`LICENSE`](LICENSE).

## Status

**v0.1** — all six v0 limitations resolved. Working reference implementation with:
- Pynauty-backed exact canonization (100% permutation invariance, 100% nx agreement)
- Oracle-verified minimal-edit certificates (100% for disconnect predicate)
- Landmark-based persistence scaling (n=1000 in ~1s)
- Rule-based perturbation algebra (betweenness, articulation, motifs)
- Smart pruning (40-50% channel reduction)
- Emitted stability-bound certificates (3 theorems, checked)
- Bitwise-determinism CI test (24/24 outputs identical across subprocesses)


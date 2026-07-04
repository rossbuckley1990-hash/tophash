# TopHash

> **The Structural Identity Layer for the AI Era.**
> From bytes to structure. From hashing to proof-grade identity.

TopHash is a structural identity primitive. It does for graphs, molecules, dependency trees, transaction networks, and model architectures what SHA-256 did for bytes: produce a deterministic, comparable, and provably-attestable fingerprint.

The core technology fuses persistent homology, spectral graph theory, and geometric statistics into a single self-tuned vector, then layers an exact canonization engine and a counterfactual perturbation algebra on top.

---

## What's in this repo

This is the **working reference implementation** of TopHash — a Python package implementing all three layers from the technical specification, plus a complete benchmark suite that validates the primitive against real public datasets across five verticals.

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

| Metric | Result |
|--------|--------|
| TopHash v3 classification accuracy (drug discovery, 10-fold CV) | **80.8%** (matches WL subtree kernel baseline) |
| TopHashX permutation invariance (all 5 verticals) | **100%** |
| TopHashX isomorphism agreement with networkx (19 test pairs) | **100%** |
| TopHash Ω∞ minimal-edit certificate discovery rate | **94%** (47/50) |
| TopHash v3 mean latency per graph | **1–3 ms** |
| TopHashX mean latency per graph | **1.9–6.2 ms** |

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

## Known limitations

The current reference implementation has four documented limitations, each with a known production solution:

1. **Canonical labeling falls back to a heuristic on graphs with large symmetry classes.** The current implementation bounds the permutation search at 1000 candidates. Graphs with larger symmetry classes (e.g., regular graphs with >7 same-degree nodes) fall back to a refinement-based ordering that is not provably canonical. *Production replacement:* Nauty-style individualization-refinement with automorphism pruning.

2. **Persistence computation scales as O(n³) on dense graphs.** The ripser backend computes Vietoris-Rips persistence over the all-pairs shortest-path matrix, which is O(n³) to compute. *Production path:* sparse shortest paths, landmark-based persistence approximation, subsampling.

3. **Perturbation algebra is exhaustive, not smart.** Ω∞ currently sweeps all 5 perturbation families × 3 scales unconditionally. *Production version:* use the invariant core to skip perturbations that cannot possibly flip the target predicate (5-10x speedup).

4. **No persistence stability theorem is currently enforced.** The proof object carries the refinement trace but does not yet emit explicit stability-bound certificates (Lipschitz constants, interleaving bounds). The mathematics is implemented; the certificate emission is not.

---

## License

MIT — see [`LICENSE`](LICENSE).

## Status

Working reference implementation. Ready for design-partner deployment.

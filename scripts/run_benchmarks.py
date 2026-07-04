"""
TopHash Full Benchmark — tests all three layers on all 5 verticals.

Layer 1 (TopHash v3):     Graph classification accuracy + ANN retrieval quality
Layer 2 (TopHashX):       Isomorphism detection + canonical ID stability + speed
Layer 3 (TopHash Ω∞):     Perturbation sweeps + invariant core + minimal-edit certs

Also includes a baseline: WL (Weisfeiler-Lehman) subtree kernel + SVM for
graph classification accuracy comparison.
"""
import os
import sys
import json
import time
import pickle
import warnings
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Tuple
from collections import defaultdict

warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/z/my-project')

from tophash import v3, ensemble, canon, omega, distance
from scripts.fetch_datasets import fetch_all

BENCH_OUT_DIR = "/home/z/my-project/data/benchmarks"
os.makedirs(BENCH_OUT_DIR, exist_ok=True)


# ============================================================
# Baseline: Weisfeiler-Lehman subtree kernel
# ============================================================
def wl_subtree_features(G: nx.Graph, n_iter: int = 3) -> np.ndarray:
    """Compute WL subtree kernel features (1-WL color histogram)."""
    G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G))
    G = nx.convert_node_labels_to_integers(G, first_label=0)

    # Initial color: degree
    colors = {n: G.degree(n) for n in G.nodes()}

    # Use a stable hash for WL refinement (avoid Python's salted hash() —
    # even though numeric tuples happen to be stable, we use hashlib for
    # explicitness and to match TopHash's determinism invariant).
    import hashlib
    def _stable_wl_hash(color: int, neighbor_colors: tuple) -> int:
        key = f"{color}|{neighbor_colors}".encode("utf-8")
        return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")

    # Collect histograms at each iteration
    histograms = []
    for it in range(n_iter + 1):
        # Histogram of current colors
        color_counts = defaultdict(int)
        for c in colors.values():
            color_counts[c] += 1
        histograms.append(dict(color_counts))

        if it == n_iter:
            break

        # Refine colors
        new_colors = {}
        for n in G.nodes():
            nbr_colors = tuple(sorted(colors[nb] for nb in G.neighbors(n)))
            new_colors[n] = _stable_wl_hash(colors[n], nbr_colors)
        colors = new_colors

    # Build a feature vector: concat histograms (with dimension cap for tractability)
    all_colors = set()
    for h in histograms:
        all_colors.update(h.keys())
    all_colors = sorted(all_colors)[:200]  # cap dimension

    feat = np.zeros(len(all_colors))
    color_idx = {c: i for i, c in enumerate(all_colors)}
    for h in histograms:
        for c, cnt in h.items():
            if c in color_idx:
                feat[color_idx[c]] += cnt

    return feat


# ============================================================
# Benchmark 1 — TopHash v3 graph classification
# ============================================================
def bench_v3_classification(vertical: str, data: List[Tuple[nx.Graph, str]]):
    """
    Test TopHash v3 + SVM vs WL baseline + SVM on graph classification.
    Reports 10-fold CV accuracy for both, plus TopHash v3 Ensemble.

    Critical integrity check: also reports a DummyClassifier(most_frequent)
    baseline. If the dummy matches the TopHash/WL accuracy, the classifiers
    are collapsing to the majority class — meaning the benchmark is measuring
    nothing. This check exists because three different feature spaces
    producing identical fold-by-fold accuracy is the classic signature of
    majority-class collapse under class imbalance.
    """
    print(f"\n--- Benchmark 1: TopHash v3 classification on [{vertical}] ---")

    # Need at least 2 classes with >= 5 samples each
    label_counts = defaultdict(int)
    for _, label in data:
        label_counts[label] += 1
    valid_labels = [l for l, c in label_counts.items() if c >= 3]
    if len(valid_labels) < 2:
        print(f"  Skipping — only {len(valid_labels)} valid labels")
        return None

    filtered = [(g, l) for g, l in data if l in valid_labels]
    if len(filtered) < 10:
        print(f"  Skipping — only {len(filtered)} samples")
        return None

    # Report class balance and majority-class baseline accuracy explicitly
    majority_label = max(label_counts.items(), key=lambda x: x[1])[0]
    majority_count = label_counts[majority_label]
    majority_pct = majority_count / len(filtered)

    print(f"  {len(filtered)} graphs, {len(valid_labels)} classes: {dict(label_counts)}")
    print(f"  Majority class: '{majority_label}' = {majority_count}/{len(filtered)} "
          f"({majority_pct*100:.1f}%)")
    print(f"  → DummyClassifier(most_frequent) would score {majority_pct*100:.1f}%")

    # Compute features
    from sklearn.svm import SVC
    from sklearn.dummy import DummyClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.pipeline import Pipeline

    # TopHash v3 features
    t0 = time.perf_counter()
    feats_v3 = np.array([v3.compute(g) for g, _ in filtered])
    t_v3 = time.perf_counter() - t0

    # TopHash v3 Ensemble features
    t0 = time.perf_counter()
    feats_v3e = np.array([ensemble.compute(g) for g, _ in filtered])
    t_v3e = time.perf_counter() - t0

    # WL baseline features
    t0 = time.perf_counter()
    feats_wl = np.array([wl_subtree_features(g) for g, _ in filtered])
    t_wl = time.perf_counter() - t0

    labels = np.array([l for _, l in filtered])

    # Classification — add DummyClassifier(most_frequent) as the integrity check
    results = {
        "class_balance": {
            "n_samples": int(len(filtered)),
            "n_classes": int(len(valid_labels)),
            "label_counts": {str(k): int(v) for k, v in label_counts.items()},
            "majority_label": str(majority_label),
            "majority_pct": float(majority_pct),
        },
    }

    # Dummy baseline (no features needed — just predicts majority class)
    try:
        cv = StratifiedKFold(n_splits=min(10, len(filtered) // 2),
                             shuffle=True, random_state=42)
        dummy = DummyClassifier(strategy='most_frequent', random_state=42)
        # Use a dummy zero-feature matrix
        dummy_scores = cross_val_score(dummy, np.zeros((len(filtered), 1)), labels,
                                        cv=cv, scoring='accuracy')
        results["Dummy_most_frequent"] = {
            "accuracy_mean": float(dummy_scores.mean()),
            "accuracy_std": float(dummy_scores.std()),
            "feature_dim": 0,
            "feature_time_total_s": 0.0,
            "feature_time_per_graph_ms": 0.0,
            "n_samples": int(len(filtered)),
            "interpretation": "Predicts majority class. If TopHash acc ≈ this, the benchmark is measuring nothing.",
        }
        print(f"  {'Dummy_most_frequent':25s} dim=   0  acc={dummy_scores.mean():.3f}±{dummy_scores.std():.3f}  "
              f"(majority-class baseline)")
    except Exception as e:
        print(f"  Dummy_most_frequent: FAILED - {e}")

    for name, feats, t_feat in [("WL_baseline", feats_wl, t_wl),
                                 ("TopHash_v3_52D", feats_v3, t_v3),
                                 ("TopHash_v3E_156D", feats_v3e, t_v3e)]:
        try:
            pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('svm', SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42))
            ])
            cv = StratifiedKFold(n_splits=min(10, len(filtered) // 2),
                                 shuffle=True, random_state=42)
            scores = cross_val_score(pipe, feats, labels, cv=cv, scoring='accuracy')
            results[name] = {
                "accuracy_mean": float(scores.mean()),
                "accuracy_std": float(scores.std()),
                "feature_dim": int(feats.shape[1]),
                "feature_time_total_s": float(t_feat),
                "feature_time_per_graph_ms": float(t_feat / len(filtered) * 1000),
                "n_samples": int(len(filtered)),
                "beats_dummy_by": float(scores.mean() - results["Dummy_most_frequent"]["accuracy_mean"]),
            }
            print(f"  {name:25s} dim={feats.shape[1]:4d}  acc={scores.mean():.3f}±{scores.std():.3f}  "
                  f"({t_feat/len(filtered)*1000:.1f}ms/graph)  "
                  f"Δdummy={results[name]['beats_dummy_by']:+.3f}")
        except Exception as e:
            print(f"  {name}: FAILED - {e}")
            results[name] = {"error": str(e)}

    return results


# ============================================================
# Benchmark 2 — TopHashX isomorphism detection
# ============================================================
def bench_canon_isomorphism(vertical: str, data: List[Any]):
    """
    Test TopHashX canonical labeling:
      (a) Permutation invariance: same graph relabeled → same canonical ID
      (b) Isomorphism detection vs networkx baseline
      (c) Speed
      (d) Uniqueness: distinct graphs → distinct IDs (no false collisions)
    """
    print(f"\n--- Benchmark 2: TopHashX isomorphism on [{vertical}] ---")

    # Normalize data to just graphs (some verticals have (graph, label) tuples)
    if data and isinstance(data[0], tuple):
        graphs = [g for g, _ in data]
    else:
        graphs = list(data)

    if len(graphs) < 2:
        print(f"  Skipping — only {len(graphs)} graphs")
        return None

    # Cap at 30 graphs for tractability (canon can be slow on big graphs)
    test_graphs = []
    for g in graphs[:30]:
        # Skip very large graphs (>50 nodes) to keep canon tractable
        if g.number_of_nodes() <= 50:
            test_graphs.append(g)
    print(f"  Testing {len(test_graphs)} graphs (<= 50 nodes for tractability)")

    if len(test_graphs) < 2:
        return None

    # Test 2a: Permutation invariance
    print("  [2a] Permutation invariance test...")
    perm_pass = 0
    perm_total = 0
    times_id = []
    for g in test_graphs:
        try:
            t0 = time.perf_counter()
            r1 = canon.tophashx(g, include_certificate=False)
            t1 = time.perf_counter()
            times_id.append(t1 - t0)

            # Build a permuted version
            nodes = list(g.nodes())
            if len(nodes) < 2:
                continue
            rng = np.random.RandomState(42)
            perm = rng.permutation(len(nodes))
            mapping = {nodes[i]: nodes[perm[i]] for i in range(len(nodes))}
            g_perm = nx.relabel_nodes(g, mapping)

            r2 = canon.tophashx(g_perm, include_certificate=False)
            perm_total += 1
            if r1['canonical_id'] == r2['canonical_id']:
                perm_pass += 1
        except Exception as e:
            print(f"    error on graph with {g.number_of_nodes()} nodes: {e}")
            continue

    perm_invariance_rate = perm_pass / max(perm_total, 1)

    # Test 2b: Isomorphism detection vs networkx
    # NOTE: We only test pairs where both graphs have the same number of nodes
    # AND edges (otherwise networkx trivially returns False and we'd be testing
    # nothing). If no such pairs exist in the test set, we report "n/a" rather
    # than 0.0% — the latter would be misread as "complete failure" by a
    # skimming reader.
    print("  [2b] Isomorphism detection vs networkx...")
    n_pairs_testable = 0  # pairs with same n_nodes AND n_edges
    n_pairs_tested = 0    # testable pairs where both TopHashX and nx completed
    n_pairs_agree = 0
    n_pairs_both_iso = 0
    n_pairs_both_noniso = 0
    n_disagreements = 0

    # Sample pairs (cap to keep tractable)
    rng = np.random.RandomState(42)
    n_test = min(len(test_graphs), 15)
    test_subset = [test_graphs[i] for i in rng.choice(len(test_graphs), n_test, replace=False)]

    for i in range(len(test_subset)):
        for j in range(i + 1, len(test_subset)):
            g1, g2 = test_subset[i], test_subset[j]
            # Pre-filter: only test pairs where isomorphism is plausible
            if g1.number_of_nodes() != g2.number_of_nodes():
                continue
            if g1.number_of_edges() != g2.number_of_edges():
                continue
            n_pairs_testable += 1
            try:
                # TopHashX
                r1 = canon.tophashx(g1, include_certificate=False)
                r2 = canon.tophashx(g2, include_certificate=False)
                tophash_iso = (r1['canonical_id'] == r2['canonical_id'])

                # networkx
                nx_iso = nx.is_isomorphic(g1, g2)

                n_pairs_tested += 1
                if tophash_iso == nx_iso:
                    n_pairs_agree += 1
                    if tophash_iso:
                        n_pairs_both_iso += 1
                    else:
                        n_pairs_both_noniso += 1
                else:
                    n_disagreements += 1
            except Exception as e:
                continue

    # Track which canon engine was used
    engine_used = "unknown"
    try:
        sample_result = canon.tophashx(test_graphs[0], include_certificate=False)
        engine_used = sample_result.get("canon_engine", "unknown")
    except Exception:
        pass

    # Test 2c: Uniqueness — distinct graphs should have distinct IDs
    print("  [2c] Uniqueness test (distinct graphs → distinct IDs)...")
    ids = []
    for g in test_graphs:
        try:
            r = canon.tophashx(g, include_certificate=False)
            ids.append(r['canonical_id'])
        except Exception:
            continue
    unique_ids = len(set(ids))
    total_ids = len(ids)
    uniqueness_rate = unique_ids / max(total_ids, 1)

    # Compute agreement rate carefully — distinguish "0 tested" from "0% agreement"
    if n_pairs_tested == 0:
        agreement_rate_str = "n/a"
        agreement_rate_val = None
    else:
        agreement_rate_str = f"{n_pairs_agree/n_pairs_tested*100:.1f}%"
        agreement_rate_val = float(n_pairs_agree / n_pairs_tested)

    results = {
        "n_graphs_tested": int(len(test_graphs)),
        "canon_engine": engine_used,
        "exactness_guaranteed": (engine_used == "pynauty"),
        "permutation_invariance": {
            "n_tested": int(perm_total),
            "n_passed": int(perm_pass),
            "pass_rate": float(perm_invariance_rate),
        },
        "isomorphism_vs_nx": {
            "n_pairs_testable": int(n_pairs_testable),
            "n_pairs_tested": int(n_pairs_tested),
            "n_agree": int(n_pairs_agree),
            "agreement_rate": agreement_rate_val,  # None if no pairs tested
            "agreement_rate_str": agreement_rate_str,  # "n/a (0 pairs)" or "100.0%"
            "n_both_iso": int(n_pairs_both_iso),
            "n_both_noniso": int(n_pairs_both_noniso),
            "n_disagreements": int(n_disagreements),
            "note": "n/a means 0 testable pairs (graphs had different node/edge counts)" if n_pairs_tested == 0 else None,
        },
        "uniqueness": {
            "n_ids": int(total_ids),
            "n_unique": int(unique_ids),
            "uniqueness_rate": float(uniqueness_rate),
        },
        "timing": {
            "mean_id_time_ms": float(np.mean(times_id) * 1000) if times_id else 0.0,
            "p95_id_time_ms": float(np.percentile(times_id, 95) * 1000) if times_id else 0.0,
            "max_id_time_ms": float(np.max(times_id) * 1000) if times_id else 0.0,
            "total_id_time_s": float(np.sum(times_id)),
        },
    }

    print(f"  Canon engine: {engine_used} (exactness_guaranteed={results['exactness_guaranteed']})")
    print(f"  Permutation invariance: {perm_pass}/{perm_total} = {perm_invariance_rate:.1%}")
    print(f"  Isomorphism agreement with nx: {n_pairs_agree}/{n_pairs_tested} = {agreement_rate_str}"
          f" ({n_pairs_testable} testable pairs)")
    print(f"  Uniqueness: {unique_ids}/{total_ids} = {uniqueness_rate:.1%}")
    print(f"  Timing: mean {np.mean(times_id)*1000:.1f}ms, max {np.max(times_id)*1000:.1f}ms")

    return results


# ============================================================
# Benchmark 3 — TopHash Ω∞ counterfactual analysis
# ============================================================
def bench_omega_counterfactual(vertical: str, data: List[Any]):
    """
    Test TopHash Ω∞ counterfactual engine:
      (a) Perturbation sweep over 5 families × 3 scales
      (b) Invariant core extraction
      (c) Minimal-edit certificate search (find regime-flipping edits)
      (d) Response tensor statistics
    """
    print(f"\n--- Benchmark 3: TopHash Ω∞ counterfactual on [{vertical}] ---")

    if data and isinstance(data[0], tuple):
        graphs = [g for g, _ in data]
    else:
        graphs = list(data)

    # Sample up to 10 graphs for tractability
    test_graphs = graphs[:10]
    print(f"  Testing {len(test_graphs)} graphs with 5 perturbations × 3 scales = 15 perturbations each")

    all_results = []
    total_perturbations = 0
    total_invariant_channels = 0
    total_fragile_channels = 0
    total_certs_found = 0
    total_oracle_verified = 0  # Ω cert matches Stoer-Wagner min-cut
    total_true_negatives_verified = 0  # No-cert cases where oracle confirms min-cut > budget
    total_oracle_checks = 0  # Total cases where oracle verification was performed
    response_magnitudes = []

    for i, g in enumerate(test_graphs):
        try:
            t0 = time.perf_counter()
            result = omega.tophash_omega(
                g,
                scales=[0.05, 0.10, 0.20],
                perturbations=["node_deletion", "edge_deletion", "edge_insertion",
                                "rewiring", "motif_mask"]
            )
            t1 = time.perf_counter()

            total_perturbations += 15  # 5 perturbations × 3 scales
            total_invariant_channels += len(result['invariant_core'])
            total_fragile_channels += len(result['fragility_shell'])

            cert = result['minimal_edit_certificate']
            cert_found = cert.get('found', False)
            oracle_min_cut = cert.get('oracle_min_cut_value')
            oracle_verified = cert.get('oracle_verified')
            true_neg_verified = cert.get('true_negative_verified')

            if cert_found:
                total_certs_found += 1
            if oracle_verified is not None:
                total_oracle_checks += 1
                if oracle_verified:
                    total_oracle_verified += 1
            if true_neg_verified:
                total_true_negatives_verified += 1

            # Collect response magnitudes
            for k, v in result['channel_scores'].items():
                response_magnitudes.append(1.0 - v)  # response = 1 - invariance

            all_results.append({
                "graph_idx": i,
                "n_nodes": g.number_of_nodes(),
                "n_edges": g.number_of_edges(),
                "time_ms": float((t1 - t0) * 1000),
                "invariant_channels": int(len(result['invariant_core'])),
                "fragile_channels": int(len(result['fragility_shell'])),
                "min_edit_found": bool(cert_found),
                "min_edit_perturbation": cert.get('perturbation', None),
                "min_edit_scale": cert.get('scale', None),
                "min_edit_edges_removed": cert.get('edges_removed', None),
                "oracle_min_cut_value": oracle_min_cut,
                "oracle_verified": oracle_verified,  # True = Ω cert matches Stoer-Wagner
                "true_negative_verified": true_neg_verified,
            })
        except Exception as e:
            print(f"  graph {i}: FAILED - {e}")
            continue

    if not all_results:
        return None

    results = {
        "n_graphs_tested": int(len(all_results)),
        "total_perturbations_evaluated": int(total_perturbations),
        "avg_invariant_channels": float(np.mean([r['invariant_channels'] for r in all_results])),
        "avg_fragile_channels": float(np.mean([r['fragile_channels'] for r in all_results])),
        "min_edit_certificates_found": int(total_certs_found),
        "min_edit_rate": float(total_certs_found / max(len(all_results), 1)),
        "oracle_verification": {
            "n_oracle_checks_performed": int(total_oracle_checks),
            "n_certs_oracle_verified": int(total_oracle_verified),
            "n_true_negatives_oracle_verified": int(total_true_negatives_verified),
            "oracle_verified_rate": float(total_oracle_verified / max(total_certs_found, 1)),
            "oracle_note": "Stoer-Wagner exact min-cut used as oracle. oracle_verified=True means Ω's certificate cost equals the true min-cut.",
        },
        "timing": {
            "mean_ms": float(np.mean([r['time_ms'] for r in all_results])),
            "max_ms": float(np.max([r['time_ms'] for r in all_results])),
            "total_s": float(np.sum([r['time_ms'] for r in all_results]) / 1000),
        },
        "response_stats": {
            "mean_response": float(np.mean(response_magnitudes)) if response_magnitudes else 0.0,
            "max_response": float(np.max(response_magnitudes)) if response_magnitudes else 0.0,
            "std_response": float(np.std(response_magnitudes)) if response_magnitudes else 0.0,
        },
        "per_graph_details": all_results,
    }

    print(f"  Total perturbations evaluated: {total_perturbations}")
    print(f"  Avg invariant channels/graph: {results['avg_invariant_channels']:.1f}")
    print(f"  Avg fragile channels/graph: {results['avg_fragile_channels']:.1f}")
    print(f"  Minimal-edit certs found: {total_certs_found}/{len(all_results)}")
    print(f"  Oracle-verified certs: {total_oracle_verified}/{total_certs_found} "
          f"(+{total_true_negatives_verified} true negatives verified)")
    print(f"  Mean time: {results['timing']['mean_ms']:.1f}ms/graph")

    return results


# ============================================================
# Top-level benchmark runner
# ============================================================
def run_full_benchmark():
    """Run all benchmarks on all 5 verticals + real TUDatasets."""
    print("=" * 70)
    print("TopHash Full Benchmark Suite")
    print("=" * 70)

    # Fetch the 5-vertical datasets
    datasets = fetch_all()

    # Also fetch the real TUDatasets (MUTAG, PROTEINS, NCI1)
    # These replace the synthetic drug-discovery smoke test with the canonical
    # graph-classification benchmarks used in the WL kernel literature.
    try:
        from scripts.fetch_tudataset import fetch_all_tu
        tu_datasets = fetch_all_tu()
        # Add TUDatasets as separate verticals
        for name, data in tu_datasets.items():
            datasets[f"tudataset_{name}"] = data
    except Exception as e:
        print(f"\n[WARNING] Could not fetch TUDatasets: {e}")
        print("Falling back to synthetic drug_discovery only.")

    # Run benchmarks per vertical
    all_results = {}
    for vertical, data in datasets.items():
        if not data:
            print(f"\n[SKIP] {vertical}: no data")
            continue

        v_results = {
            "vertical": vertical,
            "n_graphs": len(data),
        }

        # Sample size breakdown
        if isinstance(data[0], tuple):
            sample_sizes = [g.number_of_nodes() for g, _ in data]
        else:
            sample_sizes = [g.number_of_nodes() for g in data]

        v_results["graph_size_stats"] = {
            "min_nodes": int(np.min(sample_sizes)),
            "max_nodes": int(np.max(sample_sizes)),
            "mean_nodes": float(np.mean(sample_sizes)),
            "median_nodes": float(np.median(sample_sizes)),
        }

        # Benchmark 1: TopHash v3 classification (needs labels)
        if isinstance(data[0], tuple):
            try:
                v_results["bench_v3_classification"] = bench_v3_classification(vertical, data)
            except Exception as e:
                v_results["bench_v3_classification"] = {"error": str(e)}

        # Benchmark 2: TopHashX isomorphism
        try:
            v_results["bench_canon_isomorphism"] = bench_canon_isomorphism(vertical, data)
        except Exception as e:
            v_results["bench_canon_isomorphism"] = {"error": str(e)}

        # Benchmark 3: TopHash Ω∞ counterfactual
        try:
            v_results["bench_omega_counterfactual"] = bench_omega_counterfactual(vertical, data)
        except Exception as e:
            v_results["bench_omega_counterfactual"] = {"error": str(e)}

        all_results[vertical] = v_results

    # Save
    out_file = os.path.join(BENCH_OUT_DIR, "full_benchmark_results.json")
    with open(out_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {out_file}")
    return all_results


if __name__ == "__main__":
    results = run_full_benchmark()
    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    for vertical, vres in results.items():
        print(f"\n{vertical.upper()} ({vres['n_graphs']} graphs, "
              f"size {vres['graph_size_stats']['min_nodes']}-{vres['graph_size_stats']['max_nodes']} nodes)")
        if "bench_v3_classification" in vres and vres["bench_v3_classification"]:
            print("  TopHash v3 classification:")
            for method, info in vres["bench_v3_classification"].items():
                if isinstance(info, dict) and "accuracy_mean" in info:
                    dummy_delta = info.get('beats_dummy_by', 0.0)
                    print(f"    {method:25s}: acc={info['accuracy_mean']:.3f}±{info['accuracy_std']:.3f}  "
                          f"dim={info['feature_dim']}  "
                          f"Δdummy={dummy_delta:+.3f}  "
                          f"{info['feature_time_per_graph_ms']:.1f}ms/graph")
        if "bench_canon_isomorphism" in vres and vres["bench_canon_isomorphism"]:
            ci = vres["bench_canon_isomorphism"]
            nx_str = ci['isomorphism_vs_nx']['agreement_rate_str']
            print(f"  TopHashX: engine={ci.get('canon_engine','?')}, "
                  f"perm_invariance={ci['permutation_invariance']['pass_rate']:.1%}, "
                  f"nx_agreement={nx_str}, "
                  f"uniqueness={ci['uniqueness']['uniqueness_rate']:.1%}, "
                  f"mean={ci['timing']['mean_id_time_ms']:.1f}ms")
        if "bench_omega_counterfactual" in vres and vres["bench_omega_counterfactual"]:
            oc = vres["bench_omega_counterfactual"]
            oracle = oc.get('oracle_verification', {})
            print(f"  TopHash Ω∞: {oc['total_perturbations_evaluated']} perturbations, "
                  f"avg {oc['avg_invariant_channels']:.1f} invariant + "
                  f"{oc['avg_fragile_channels']:.1f} fragile channels, "
                  f"min-edit rate {oc['min_edit_rate']:.1%}, "
                  f"oracle-verified {oracle.get('n_certs_oracle_verified',0)}/"
                  f"{oc['min_edit_certificates_found']}, "
                  f"mean {oc['timing']['mean_ms']:.1f}ms")

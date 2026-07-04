"""
TopHash Determinism CI Test — the sacred invariant.

Runs the full TopHash pipeline (v3 + ensemble + canon + omega) twice in two
completely separate Python processes with different PYTHONHASHSEED values,
then asserts that the outputs are bitwise-identical.

This test exists because Python's built-in hash() is salted per-process for
strings (PYTHONHASHSEED, since Python 3.3). Any use of hash() on a string
or a tuple containing a string produces different values across interpreter
restarts, which silently breaks cross-process reproducibility — the core
of TopHash's "deterministic, training-free, reproducible across machines"
positioning.

If this test ever fails, the brand is broken. Fix the offending hash() call
before merging.

Usage:
    python3 scripts/test_determinism.py

Exit code 0 = PASS (bitwise-identical across processes)
Exit code 1 = FAIL (drift detected — see diff output)
"""
import os
import sys
import json
import subprocess
import tempfile
import hashlib

# Add project to path
sys.path.insert(0, '/home/z/my-project')


def _run_pipeline_in_subprocess(output_path: str, pythonhashseed: str) -> dict:
    """
    Run the TopHash pipeline in a fresh subprocess with a specific PYTHONHASHSEED.

    The subprocess computes fingerprints, canonical IDs, and Ω∞ dossiers for
    a fixed set of test graphs, then writes the results (as JSON) to output_path.
    """
    # Use string concatenation to avoid f-string escaping issues with the
    # nested {name} placeholders in the subprocess code.
    script = '''
import os, sys, json
sys.path.insert(0, '/home/z/my-project')
os.environ['PYTHONHASHSEED'] = '__SEED__'

import numpy as np
import networkx as nx
from tophash import v3, ensemble, canon, omega

# Fixed test set — deterministic graphs, no RNG dependence in the input
graphs = {
    "cycle_10": nx.cycle_graph(10),
    "path_10": nx.path_graph(10),
    "complete_5": nx.complete_graph(5),
    "karate": nx.karate_club_graph(),
    "petersen": nx.petersen_graph(),
    "grid_3x3": nx.grid_2d_graph(3, 3),
}

results = {}

# Layer 1: TopHash v3 fingerprints (must be bitwise-identical across processes)
for name, G in graphs.items():
    fp = v3.compute(G)
    results["v3_" + name] = {
        "fingerprint_hex": fp.tobytes().hex(),
        "fingerprint_shape": list(fp.shape),
    }

# Layer 1b: Ensemble
for name, G in graphs.items():
    fp_e = ensemble.compute(G)
    results["ensemble_" + name] = {
        "fingerprint_hex": fp_e.tobytes().hex(),
    }

# Layer 2: TopHashX canonical IDs
for name, G in graphs.items():
    r = canon.tophashx(G, include_certificate=False)
    results["canon_" + name] = {
        "canonical_id": r["canonical_id"],
        "canon_engine": r["canon_engine"],
        "exactness_guaranteed": r["exactness_guaranteed"],
    }

# Layer 3: TopHash Ω∞ — perturbation sweeps
# This is where the hash-seeding bug would manifest (perturbation families
# seeded with string-keyed hash() would produce different perturbed graphs
# across processes, leading to different response tensors).
for name, G in graphs.items():
    dossier = omega.tophash_omega(G, scales=[0.05, 0.10, 0.20])
    results["omega_" + name] = {
        "base_fingerprint_hex": dossier["base_fingerprint"].tobytes().hex(),
        "invariant_core_count": len(dossier["invariant_core"]),
        "fragility_shell_count": len(dossier["fragility_shell"]),
        "min_edit_found": dossier["minimal_edit_certificate"]["found"],
        "min_edit_perturbation": dossier["minimal_edit_certificate"].get("perturbation"),
        "min_edit_scale": dossier["minimal_edit_certificate"].get("scale"),
        "oracle_min_cut_value": dossier["minimal_edit_certificate"].get("oracle_min_cut_value"),
        "oracle_verified": dossier["minimal_edit_certificate"].get("oracle_verified"),
    }
    # Also include the channel scores — these are the most sensitive to seed drift
    channel_scores = dossier["channel_scores"]
    results["omega_" + name]["channel_scores"] = dict(sorted(channel_scores.items()))

# Write results to the output file
with open("__OUT__", "w") as f:
    json.dump(results, f, indent=2, sort_keys=True)

print("Subprocess (PYTHONHASHSEED=__SEED__) wrote " + str(len(results)) + " results to __OUT__")
'''.replace('__SEED__', pythonhashseed).replace('__OUT__', output_path)

    env = os.environ.copy()
    env['PYTHONHASHSEED'] = pythonhashseed
    result = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True, text=True, env=env, timeout=300
    )
    if result.returncode != 0:
        print(f"Subprocess FAILED (PYTHONHASHSEED={pythonhashseed}):")
        print(result.stderr)
        sys.exit(1)
    print(result.stdout.strip())

    with open(output_path) as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("TopHash Determinism CI Test")
    print("=" * 70)
    print()
    print("Running the full pipeline in two subprocesses with different PYTHONHASHSEED...")
    print("If any output differs, the determinism claim is false and must be fixed.")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        out1 = os.path.join(tmpdir, "run1.json")
        out2 = os.path.join(tmpdir, "run2.json")

        # Two different PYTHONHASHSEED values to force string-hash salting to differ
        run1 = _run_pipeline_in_subprocess(out1, "0")
        run2 = _run_pipeline_in_subprocess(out2, "12345")

        # Compare bitwise
        all_keys = sorted(set(run1.keys()) | set(run2.keys()))
        diffs = []
        for key in all_keys:
            if key not in run1:
                diffs.append((key, "MISSING_IN_RUN1", run2[key]))
            elif key not in run2:
                diffs.append((key, run1[key], "MISSING_IN_RUN2"))
            elif run1[key] != run2[key]:
                diffs.append((key, run1[key], run2[key]))

        print()
        print("=" * 70)
        if not diffs:
            print(f"✓ PASS — {len(all_keys)} outputs bitwise-identical across two subprocesses")
            print(f"  (PYTHONHASHSEED=0 vs PYTHONHASHSEED=12345)")
            print()
            print("Determinism invariant holds. The brand claim is true.")
            print("TopHash v3, TopHashX, and TopHash Ω∞ all produce reproducible output")
            print("across independent Python processes with different hash seeds.")
            print()
            # Report engine
            sample = run1.get("canon_cycle_10", {})
            print(f"  Canon engine: {sample.get('canon_engine', 'unknown')}")
            print(f"  Exactness guaranteed: {sample.get('exactness_guaranteed', 'unknown')}")
            return 0
        else:
            print(f"✗ FAIL — {len(diffs)} outputs differ across subprocesses")
            print()
            print("Determinism invariant BROKEN. The brand claim is false. Fix before merging.")
            print()
            for key, v1, v2 in diffs[:10]:
                print(f"  {key}:")
                print(f"    run1: {v1}")
                print(f"    run2: {v2}")
                print()
            if len(diffs) > 10:
                print(f"  ... and {len(diffs) - 10} more differences")
            return 1


if __name__ == "__main__":
    sys.exit(main())

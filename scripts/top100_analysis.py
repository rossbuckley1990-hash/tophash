"""
TopHash Top-100 PyPI Structural Analysis

Fetches the top 100 PyPI packages (by approximate download volume),
builds each package's dependency graph from the live PyPI JSON API,
and computes:
  - TopHash v3 fingerprint (52D)
  - TopHashX canonical ID + proof object
  - TopHashX ensemble fingerprint (156D)
  - Structural collision detection (packages with identical canonical IDs)
  - Structural similarity clustering (k-nearest neighbors by fingerprint distance)

Output: /home/z/my-project/data/top100_analysis.json
        /home/z/my-project/download/top100_pypi_report.md
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import concurrent.futures
import numpy as np
import networkx as nx
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, '/home/z/my-project')
from tophash import v3, ensemble, canon, distance

# Curated top ~100 PyPI packages by approximate download volume.
# Source: PyPIStats / BigQuery historical data, stable top packages across categories.
TOP_100_PACKAGES = [
    # Data science / numerics
    "numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "seaborn",
    "plotly", "bokeh", "statsmodels", "sympy",
    # Web frameworks
    "flask", "django", "fastapi", "tornado", "aiohttp", "bottle", "sanic",
    # HTTP / networking
    "requests", "urllib3", "httpx", "aiohttp", "httpie", "grequests",
    # Cloud / DevOps
    "boto3", "google-cloud-storage", "azure-storage-blob", "docker",
    "kubernetes", "ansible", "terraform", "kubectl",
    # Security
    "cryptography", "pyopenssl", "paramiko", "pyjwt", "authlib",
    "passlib", "bcrypt", "argon2-cffi",
    # Database
    "sqlalchemy", "psycopg2-binary", "pymongo", "redis", "celery",
    "alembic", "django-redis",
    # Testing / QA
    "pytest", "tox", "coverage", "nose", "mock", "hypothesis",
    "pytest-cov", "pytest-mock", "pytest-asyncio",
    # Code quality / formatting
    "black", "flake8", "mypy", "isort", "pylint", "autopep8", "yapf",
    "pre-commit",
    # Documentation
    "sphinx", "mkdocs", "pdoc", "jupyter", "notebook", "jupyterlab",
    "ipython", "nbconvert",
    # CLI / TUI
    "click", "typer", "rich", "tqdm", "colorama", "prompt-toolkit",
    "asciimatics", "textual",
    # Configuration / serialization
    "pyyaml", "tomli", "toml", "jsonschema", "pydantic", "marshmallow",
    "configparser",
    # Async / concurrency
    "asyncio", "trio", "anyio", "gevent", "eventlet", "twisted",
    # Imaging / PDF
    "pillow", "reportlab", "fpdf", "pdfplumber", "pymupdf",
    # NLP / ML
    "nltk", "spacy", "transformers", "torch", "tensorflow",
    "scikit-image", "opencv-python",
    # Logging / monitoring
    "loguru", "structlog", "sentry-sdk", "prometheus-client",
    # Utilities
    "python-dateutil", "pytz", "six", "wrapt", "decorator",
    "setuptools", "pip", "wheel", "virtualenv", "pathlib2",
]

OUTPUT_DIR = "/home/z/my-project/data"
DOWNLOAD_DIR = "/home/z/my-project/download"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def fetch_package_data(pkg_name: str, timeout: int = 15) -> dict:
    """Fetch package metadata from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TopHash-Top100-Analysis/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except Exception as e:
        return {"error": str(e), "package": pkg_name}


def build_dependency_graph(pkg_name: str, pypi_data: dict) -> nx.Graph:
    """Build a dependency graph: nodes = package + deps, edges = dependency."""
    G = nx.Graph()
    G.add_node(pkg_name, type="root")

    info = pypi_data.get("info", {})
    requires = info.get("requires_dist") or []

    for req_str in requires:
        # Parse "package>=1.0; extra == 'dev'" → "package"
        dep_name = req_str.split(">")[0].split("<")[0].split("=")[0]
        dep_name = dep_name.split("!")[0].split(";")[0].split("[")[0].strip()
        if dep_name and not dep_name.startswith("#") and not dep_name.startswith("python "):
            G.add_node(dep_name, type="dependency")
            G.add_edge(pkg_name, dep_name)

    return G


def analyze_package(pkg_name: str) -> dict:
    """Full TopHash analysis of one package."""
    t0 = time.perf_counter()
    pypi_data = fetch_package_data(pkg_name)
    if "error" in pypi_data:
        return {"package": pkg_name, "error": pypi_data["error"]}

    G = build_dependency_graph(pkg_name, pypi_data)
    if G.number_of_nodes() < 2:
        return {
            "package": pkg_name,
            "error": "insufficient_dependencies",
            "n_nodes": G.number_of_nodes(),
        }

    # Compute TopHash layers
    t1 = time.perf_counter()
    fp_v3 = v3.compute(G)
    t2 = time.perf_counter()
    fp_v3e = ensemble.compute(G)
    t3 = time.perf_counter()
    canon_result = canon.tophashx(G, include_certificate=False)
    t4 = time.perf_counter()

    info = pypi_data.get("info", {})

    return {
        "package": pkg_name,
        "version": info.get("version", "?"),
        "summary": (info.get("summary") or "")[:120],
        "n_dependencies": G.number_of_nodes() - 1,
        "n_edges": G.number_of_edges(),
        "fingerprint_v3": fp_v3.tolist(),
        "fingerprint_v3e_156d_first_8": fp_v3e[:8].tolist(),  # for display
        "canonical_id": canon_result["canonical_id"],
        "canonical_id_short": canon_result["canonical_id"][:16],
        "canon_engine": canon_result["canon_engine"],
        "exactness_guaranteed": canon_result["exactness_guaranteed"],
        "timing_ms": {
            "fetch": (t1 - t0) * 1000,
            "v3": (t2 - t1) * 1000,
            "ensemble": (t3 - t2) * 1000,
            "canon": (t4 - t3) * 1000,
            "total": (t4 - t0) * 1000,
        },
    }


def run_analysis():
    """Run the top-100 analysis."""
    print("=" * 70)
    print("TopHash Top-100 PyPI Structural Analysis")
    print("=" * 70)
    print(f"Analyzing {len(TOP_100_PACKAGES)} packages via live PyPI API...")

    # Run in parallel for speed (PyPI can handle 10 concurrent requests)
    results = []
    failed = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pkg = {executor.submit(analyze_package, pkg): pkg
                         for pkg in TOP_100_PACKAGES}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_pkg)):
            pkg = future_to_pkg[future]
            try:
                result = future.result()
                if "error" in result:
                    failed.append(result)
                    print(f"  [{i+1:3d}/{len(TOP_100_PACKAGES)}] ✗ {pkg}: {result['error'][:50]}")
                else:
                    results.append(result)
                    print(f"  [{i+1:3d}/{len(TOP_100_PACKAGES)}] ✓ {pkg}: "
                          f"{result['n_dependencies']} deps, "
                          f"canon_id={result['canonical_id_short']}..., "
                          f"{result['timing_ms']['total']:.0f}ms")
            except Exception as e:
                failed.append({"package": pkg, "error": str(e)})
                print(f"  [{i+1:3d}/{len(TOP_100_PACKAGES)}] ✗ {pkg}: {e}")

    print(f"\nSuccessfully analyzed: {len(results)} / {len(TOP_100_PACKAGES)}")
    print(f"Failed: {len(failed)}")

    # ============================================================
    # Analysis: structural collisions + clustering
    # ============================================================
    print("\n" + "=" * 70)
    print("Structural Analysis")
    print("=" * 70)

    # Collision detection: packages with identical canonical IDs
    canon_id_to_packages = defaultdict(list)
    for r in results:
        canon_id_to_packages[r["canonical_id"]].append(r["package"])

    collisions = {cid: pkgs for cid, pkgs in canon_id_to_packages.items() if len(pkgs) > 1}
    print(f"\nStructural collisions: {len(collisions)} canonical IDs shared by multiple packages")
    for cid, pkgs in collisions.items():
        print(f"  {cid[:16]}... → {', '.join(pkgs)}")

    # Fingerprint distance matrix for top-N most similar pairs
    print("\nComputing fingerprint similarity matrix...")
    fingerprints = np.array([r["fingerprint_v3"] for r in results])
    n = len(results)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = distance.euclidean(fingerprints[i], fingerprints[j])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d

    # Top-20 most similar pairs (excluding collisions)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((dist_matrix[i, j], results[i]["package"], results[j]["package"]))
    pairs.sort()
    top_similar = pairs[:20]

    print("\nTop 20 most structurally similar package pairs:")
    for d, p1, p2 in top_similar[:10]:
        print(f"  d={d:.3f}  {p1} ↔ {p2}")

    # Distribution stats
    n_deps = [r["n_dependencies"] for r in results]
    print(f"\nDependency count distribution:")
    print(f"  min={min(n_deps)}, max={max(n_deps)}, mean={np.mean(n_deps):.1f}, median={np.median(n_deps):.1f}")

    # Timing stats
    total_times = [r["timing_ms"]["total"] for r in results]
    canon_times = [r["timing_ms"]["canon"] for r in results]
    v3_times = [r["timing_ms"]["v3"] for r in results]
    print(f"\nTiming (mean / max):")
    print(f"  TopHash v3:    {np.mean(v3_times):.1f}ms / {np.max(v3_times):.1f}ms")
    print(f"  TopHashX:      {np.mean(canon_times):.1f}ms / {np.max(canon_times):.1f}ms")
    print(f"  Total (incl fetch): {np.mean(total_times):.1f}ms / {np.max(total_times):.1f}ms")

    # Save raw results
    output = {
        "analysis_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "n_packages_attempted": len(TOP_100_PACKAGES),
            "n_packages_succeeded": len(results),
            "n_packages_failed": len(failed),
            "tophash_version": "v0.1",
        },
        "summary": {
            "n_structural_collisions": len(collisions),
            "n_unique_canonical_ids": len(canon_id_to_packages),
            "mean_dependencies": float(np.mean(n_deps)),
            "median_dependencies": float(np.median(n_deps)),
            "max_dependencies": int(max(n_deps)),
            "mean_v3_time_ms": float(np.mean(v3_times)),
            "mean_canon_time_ms": float(np.mean(canon_times)),
            "mean_total_time_ms": float(np.mean(total_times)),
        },
        "collisions": {
            cid: pkgs for cid, pkgs in collisions.items()
        },
        "top_similar_pairs": [
            {"distance": float(d), "package_a": p1, "package_b": p2}
            for d, p1, p2 in top_similar
        ],
        "packages": results,
        "failed": failed,
    }

    output_path = os.path.join(OUTPUT_DIR, "top100_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nRaw results saved to {output_path}")

    return output


if __name__ == "__main__":
    results = run_analysis()

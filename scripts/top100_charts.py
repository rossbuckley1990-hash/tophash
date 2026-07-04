"""
Generate charts for the Top-100 PyPI analysis blog post.
"""
import json
import os
import numpy as np
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

BG = "#0A0E1A"
PRIMARY = "#E8ECF4"
ACCENT = "#7C5CFF"
ACCENT_2 = "#4DD9FF"
ACCENT_3 = "#FF6FB5"
DIM = "#6E7691"

CHART_DIR = "/home/z/my-project/data/benchmarks/charts"
os.makedirs(CHART_DIR, exist_ok=True)

with open("/home/z/my-project/data/top100_analysis.json") as f:
    data = json.load(f)


def chart_1_collision_distribution():
    """Bar chart: packages per collision group, showing 86/100 packages collide."""
    collisions = data["collisions"]
    summary = data["summary"]

    # Sort collision groups by size descending
    group_sizes = sorted([len(pkgs) for pkgs in collisions.values()], reverse=True)
    n_singletons = 100 - sum(group_sizes)  # packages not in any collision group

    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor=BG)
    ax.set_facecolor(BG)

    bars = ax.bar(range(len(group_sizes)), group_sizes, color=ACCENT, edgecolor='none', label='Collision groups')
    ax.bar([len(group_sizes)], [n_singletons], color=ACCENT_2, edgecolor='none', label='Singletons (unique structure)')

    ax.set_ylabel('Packages in group', color=PRIMARY, fontsize=11)
    ax.set_title('Top-100 PyPI: 86 of 100 packages share structural skeletons\n'
                 '(dependency-graph isomorphism groups)',
                 color=PRIMARY, fontsize=12, fontweight='bold', pad=14)
    ax.set_xticks(range(len(group_sizes) + 1))
    ax.set_xticklabels([f'G{i+1}' for i in range(len(group_sizes))] + ['Unique'],
                       color=PRIMARY, fontsize=8, rotation=45)
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='upper right', frameon=False, fontsize=10, labelcolor=PRIMARY)

    # Annotate
    ax.text(0.5, 0.95, f'86/100 packages in collision groups\n14/100 have unique structure',
            transform=ax.transAxes, color=ACCENT_2, fontsize=11, fontweight='bold',
            verticalalignment='top', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#11172A', edgecolor=ACCENT_2, alpha=0.9))

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "top100_collisions.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_2_dependency_distribution():
    """Histogram: dependency count distribution."""
    packages = data["packages"]
    dep_counts = [p["n_dependencies"] for p in packages]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    ax.set_facecolor(BG)

    n, bins, patches = ax.hist(dep_counts, bins=20, color=ACCENT, edgecolor='none', alpha=0.8)

    # Color the star-graph region (1-5 deps) differently
    for i, patch in enumerate(patches):
        if bins[i] < 6:
            patch.set_facecolor(ACCENT_3)

    ax.axvline(x=5, color=DIM, linestyle='--', alpha=0.5, label='Star-graph threshold (≤5 deps)')

    ax.set_xlabel('Number of dependencies', color=PRIMARY, fontsize=11)
    ax.set_ylabel('Number of packages', color=PRIMARY, fontsize=11)
    ax.set_title('Top-100 PyPI: dependency count distribution\n'
                 'Most packages have ≤5 deps → isomorphic star graphs',
                 color=PRIMARY, fontsize=12, fontweight='bold', pad=14)
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='upper right', frameon=False, fontsize=10, labelcolor=PRIMARY)

    n_star = sum(1 for d in dep_counts if d <= 5)
    ax.text(0.65, 0.7, f'{n_star}/100 packages have ≤5 deps\n→ structurally isomorphic star graphs',
            transform=ax.transAxes, color=ACCENT_3, fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#11172A', edgecolor=ACCENT_3, alpha=0.9))

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "top100_dep_distribution.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_3_timing():
    """Bar chart: timing per package (sorted)."""
    packages = data["packages"]
    # Sort by total time
    sorted_pkgs = sorted(packages, key=lambda p: p["timing_ms"]["total"])
    total_times = [p["timing_ms"]["total"] for p in sorted_pkgs]
    v3_times = [p["timing_ms"]["v3"] for p in sorted_pkgs]
    canon_times = [p["timing_ms"]["canon"] for p in sorted_pkgs]

    fig, ax = plt.subplots(figsize=(11, 5), facecolor=BG)
    ax.set_facecolor(BG)

    x = range(len(sorted_pkgs))
    ax.bar(x, total_times, color=DIM, edgecolor='none', alpha=0.4, label='Total (incl. PyPI fetch)')
    ax.bar(x, v3_times, color=ACCENT, edgecolor='none', label='TopHash v3 (52D fingerprint)')
    ax.bar(x, canon_times, color=ACCENT_2, edgecolor='none', label='TopHashX (canonical ID)')

    ax.set_xlabel('Packages (sorted by total time)', color=PRIMARY, fontsize=11)
    ax.set_ylabel('Time (ms)', color=PRIMARY, fontsize=11)
    ax.set_title('Top-100 PyPI: per-package TopHash timing\n'
                 f'Mean: v3={np.mean(v3_times):.1f}ms, canon={np.mean(canon_times):.1f}ms, '
                 f'total={np.mean(total_times):.0f}ms (incl. network)',
                 color=PRIMARY, fontsize=12, fontweight='bold', pad=14)
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='upper left', frameon=False, fontsize=9, labelcolor=PRIMARY)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "top100_timing.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


if __name__ == "__main__":
    print("Generating Top-100 PyPI analysis charts...")
    chart_1_collision_distribution()
    chart_2_dependency_distribution()
    chart_3_timing()
    print(f"\nAll charts saved to {CHART_DIR}")

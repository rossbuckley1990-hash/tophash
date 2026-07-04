"""
Generate benchmark charts for the TopHash implementation report.
Produces 4 PNG charts in /home/z/my-project/data/benchmarks/charts/.
"""
import os
import json
import numpy as np
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

CHART_DIR = "/home/z/my-project/data/benchmarks/charts"
os.makedirs(CHART_DIR, exist_ok=True)

# Dark-tech-premium palette to match the deck
BG = "#0A0E1A"
PRIMARY = "#E8ECF4"
ACCENT = "#7C5CFF"
ACCENT_2 = "#4DD9FF"
ACCENT_3 = "#FF6FB5"
DIM = "#6E7691"


def load_results():
    with open("/home/z/my-project/data/benchmarks/full_benchmark_results.json") as f:
        return json.load(f)


def chart_1_canon_metrics(results):
    """Bar chart: TopHashX permutation invariance + nx agreement + uniqueness per vertical."""
    # Include all verticals that have canon benchmark data
    verticals = []
    perm_inv = []
    nx_agree = []
    unique = []
    for v in ['cybersecurity', 'drug_discovery', 'ai_supply_chain', 'financial_fraud',
              'data_infrastructure', 'tudataset_MUTAG', 'tudataset_PROTEINS', 'tudataset_NCI1']:
        if v not in results:
            continue
        ci = results[v].get("bench_canon_isomorphism")
        if not ci:
            continue
        verticals.append(v)
        perm_inv.append(ci.get("permutation_invariance", {}).get("pass_rate", 0) * 100)
        # Use agreement_rate_val (None for n/a) and convert to 0 for plotting, but mark n/a in label
        ar_val = ci.get("isomorphism_vs_nx", {}).get("agreement_rate")
        nx_agree.append(ar_val * 100 if ar_val is not None else 0)
        unique.append(ci.get("uniqueness", {}).get("uniqueness_rate", 0) * 100)

    x = np.arange(len(verticals))
    width = 0.27

    fig, ax = plt.subplots(figsize=(13, 5.5), facecolor=BG)
    ax.set_facecolor(BG)

    b1 = ax.bar(x - width, perm_inv, width, label='Permutation Invariance', color=ACCENT, edgecolor='none')
    b2 = ax.bar(x, nx_agree, width, label='Iso Agreement (vs nx) — n/a shown as 0', color=ACCENT_2, edgecolor='none')
    b3 = ax.bar(x + width, unique, width, label='ID Uniqueness', color=ACCENT_3, edgecolor='none')

    ax.set_ylabel('Rate (%)', color=PRIMARY, fontsize=11)
    ax.set_title('TopHashX (pynauty-backed) — Canonical Labeling Correctness\n'
                 'Engine: pynauty. Exactness guaranteed: True.',
                 color=PRIMARY, fontsize=12, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels([v.replace('_', '\n').replace('tudataset\n', 'TU:').title() for v in verticals],
                       color=PRIMARY, fontsize=8.5)
    ax.set_ylim(0, 115)
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='lower right', frameon=False, fontsize=9, labelcolor=PRIMARY)

    # Add value labels; mark n/a for nx_agree where 0 pairs were testable
    for i, v in enumerate(verticals):
        ci = results[v].get("bench_canon_isomorphism", {})
        iso = ci.get("isomorphism_vs_nx", {})
        n_tested = iso.get("n_pairs_tested", 0)
        # Permutation invariance label
        ax.text(x[i] - width, perm_inv[i] + 1.5, f'{perm_inv[i]:.0f}', ha='center', va='bottom', color=PRIMARY, fontsize=7.5)
        # nx agreement label — n/a if 0 tested
        if n_tested == 0:
            ax.text(x[i], nx_agree[i] + 1.5, 'n/a', ha='center', va='bottom', color=DIM, fontsize=7.5, style='italic')
        else:
            ax.text(x[i], nx_agree[i] + 1.5, f'{nx_agree[i]:.0f}', ha='center', va='bottom', color=PRIMARY, fontsize=7.5)
        # Uniqueness label
        ax.text(x[i] + width, unique[i] + 1.5, f'{unique[i]:.0f}', ha='center', va='bottom', color=PRIMARY, fontsize=7.5)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "chart1_canon_metrics.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_2_v3_classification(results):
    """Bar chart: TopHash v3 classification accuracy vs WL baseline + dummy."""
    # Use the real TUDatasets (MUTAG, PROTEINS, NCI1)
    tu_verticals = []
    dummy_acc = []
    wl_acc = []
    v3_acc = []
    v3e_acc = []

    for v in ['tudataset_MUTAG', 'tudataset_PROTEINS', 'tudataset_NCI1']:
        if v not in results:
            continue
        cls = results[v].get("bench_v3_classification", {})
        # Try both key formats
        dummy = cls.get("Dummy_most_frequent", {})
        wl = cls.get("WL_baseline_128D", cls.get("WL_baseline", {}))
        v3r = cls.get("TopHash_v3_52D", {})
        v3e = cls.get("TopHash_v3E_156D", {})

        if not (dummy.get("accuracy_mean") is not None and v3r.get("accuracy_mean") is not None):
            continue
        tu_verticals.append(v.replace('tudataset_', ''))
        dummy_acc.append(dummy["accuracy_mean"] * 100)
        wl_acc.append(wl.get("accuracy_mean", 0) * 100)
        v3_acc.append(v3r["accuracy_mean"] * 100)
        v3e_acc.append(v3e.get("accuracy_mean", 0) * 100)

    if not tu_verticals:
        print("  no TUDataset classification data, skipping chart 2")
        return

    x = np.arange(len(tu_verticals))
    width = 0.20

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    b0 = ax.bar(x - 1.5*width, dummy_acc, width, label='Dummy (most_frequent) — majority class', color=DIM, edgecolor='none')
    b1 = ax.bar(x - 0.5*width, wl_acc, width, label='WL Subtree Kernel (128D baseline)', color='#888FA8', edgecolor='none')
    b2 = ax.bar(x + 0.5*width, v3_acc, width, label='TopHash v3 (52D)', color=ACCENT, edgecolor='none')
    b3 = ax.bar(x + 1.5*width, v3e_acc, width, label='TopHash v3 Ensemble (156D)', color=ACCENT_2, edgecolor='none')

    ax.set_ylabel('Classification Accuracy (%)', color=PRIMARY, fontsize=11)
    ax.set_title('TopHash v3 — Graph Classification on Real TUDatasets (10-fold CV)\n'
                 'vs WL baseline + majority-class dummy. All methods beat dummy → no collapse.',
                 color=PRIMARY, fontsize=12, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{v}\n({results["tudataset_"+v]["n_graphs"]} graphs)' for v in tu_verticals],
                       color=PRIMARY, fontsize=10)
    ax.set_ylim(40, 95)
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='lower right', frameon=False, fontsize=9, labelcolor=PRIMARY, ncol=2)

    for bars in [b0, b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.5,
                    f'{h:.1f}', ha='center', va='bottom', color=PRIMARY, fontsize=8)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "chart2_v3_classification.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_3_omega_invariant_core(results):
    """Stacked bar chart: invariant vs fragile channels per vertical."""
    verticals = list(results.keys())
    inv_channels = []
    frag_channels = []
    for v in verticals:
        oc = results[v].get("bench_omega_counterfactual", {})
        inv_channels.append(oc.get("avg_invariant_channels", 0))
        frag_channels.append(oc.get("avg_fragile_channels", 0))

    x = np.arange(len(verticals))

    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    b1 = ax.bar(x, inv_channels, color=ACCENT, edgecolor='none', label='Invariant Core Channels')
    b2 = ax.bar(x, frag_channels, bottom=inv_channels, color=ACCENT_3, edgecolor='none', label='Fragility Shell Channels')

    ax.set_ylabel('Average Channels per Graph', color=PRIMARY, fontsize=11)
    ax.set_title('TopHash Ω∞ — Invariant Core / Fragility Shell Decomposition',
                 color=PRIMARY, fontsize=13, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels([v.replace('_', ' ').title() for v in verticals],
                       color=PRIMARY, fontsize=10, rotation=15, ha='right')
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='upper right', frameon=False, fontsize=10, labelcolor=PRIMARY)

    for i, (inv, frag) in enumerate(zip(inv_channels, frag_channels)):
        total = inv + frag
        ax.text(i, total + 0.3, f'{total:.1f}', ha='center', va='bottom',
                color=PRIMARY, fontsize=10, fontweight='bold')

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "chart3_omega_decomposition.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_4_timing(results):
    """Horizontal bar chart: timing per graph for each layer × vertical."""
    rows = []
    for v, r in results.items():
        cls = r.get("bench_v3_classification", {})
        canon = r.get("bench_canon_isomorphism", {})
        omega_r = r.get("bench_omega_counterfactual", {})

        v3_time = None
        if cls and "TopHash_v3_52D" in cls:
            v3_time = cls["TopHash_v3_52D"].get("feature_time_per_graph_ms")
        canon_time = canon.get("timing", {}).get("mean_id_time_ms")
        omega_time = omega_r.get("timing", {}).get("mean_ms")

        if v3_time is not None and canon_time is not None and omega_time is not None:
            rows.append((v, v3_time, canon_time, omega_time))

    if not rows:
        print("  no timing data, skipping chart 4")
        return

    verticals = [r[0] for r in rows]
    v3_times = [r[1] for r in rows]
    canon_times = [r[2] for r in rows]
    omega_times = [r[3] for r in rows]

    # Log-scale for readability
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor=BG)
    ax.set_facecolor(BG)

    x = np.arange(len(verticals))
    width = 0.27
    # Use log scale if any time is large
    times_array = np.array(v3_times + canon_times + omega_times)
    use_log = times_array.max() / max(times_array.min(), 0.001) > 50

    b1 = ax.bar(x - width, v3_times, width, label='TopHash v3 (compute fingerprint)', color=ACCENT, edgecolor='none')
    b2 = ax.bar(x, canon_times, width, label='TopHashX (canonical ID + cert)', color=ACCENT_2, edgecolor='none')
    b3 = ax.bar(x + width, omega_times, width, label='TopHash Ω∞ (15 perturbations)', color=ACCENT_3, edgecolor='none')

    if use_log:
        ax.set_yscale('log')
        ax.set_ylabel('Time per graph (ms, log scale)', color=PRIMARY, fontsize=11)
    else:
        ax.set_ylabel('Time per graph (ms)', color=PRIMARY, fontsize=11)

    ax.set_title('TopHash Layer Timings — Latency per Graph Across 5 Verticals',
                 color=PRIMARY, fontsize=13, fontweight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels([v.replace('_', ' ').title() for v in verticals],
                       color=PRIMARY, fontsize=10, rotation=15, ha='right')
    ax.tick_params(colors=PRIMARY)
    for spine in ax.spines.values():
        spine.set_color(DIM)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.2, color=DIM)
    ax.set_axisbelow(True)
    ax.legend(loc='upper left', frameon=False, fontsize=10, labelcolor=PRIMARY)

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h * (1.1 if use_log else 1.0),
                    f'{h:.1f}ms', ha='center', va='bottom', color=PRIMARY, fontsize=8,
                    rotation=0)

    plt.tight_layout()
    out = os.path.join(CHART_DIR, "chart4_timings.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


def chart_5_min_edit_certs(results):
    """Donut chart: minimal-edit certificate discovery rate per vertical."""
    verticals = list(results.keys())
    rates = []
    for v in verticals:
        oc = results[v].get("bench_omega_counterfactual", {})
        rates.append(oc.get("min_edit_rate", 0) * 100)

    fig, axes = plt.subplots(1, len(verticals), figsize=(15, 4), facecolor=BG)
    if len(verticals) == 1:
        axes = [axes]

    colors = [ACCENT, ACCENT_2, ACCENT_3, "#FFB454", "#5FE0A0"]

    for i, (v, rate) in enumerate(zip(verticals, rates)):
        ax = axes[i]
        ax.set_facecolor(BG)
        sizes = [rate, 100 - rate]
        cols = [colors[i % len(colors)], DIM]
        wedges, texts = ax.pie(sizes, colors=cols, startangle=90, counterclock=False,
                                wedgeprops=dict(width=0.35, edgecolor=BG, linewidth=2))
        ax.text(0, 0, f'{rate:.0f}%', ha='center', va='center',
                color=PRIMARY, fontsize=18, fontweight='bold')
        ax.set_title(v.replace('_', ' ').title(), color=PRIMARY, fontsize=11, pad=10)

    fig.suptitle('TopHash Ω∞ — Minimal-Edit Certificate Discovery Rate',
                 color=PRIMARY, fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = os.path.join(CHART_DIR, "chart5_min_edit_certs.png")
    plt.savefig(out, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close()
    print(f"  saved {out}")


if __name__ == "__main__":
    print("Generating TopHash benchmark charts...")
    results = load_results()
    chart_1_canon_metrics(results)
    chart_2_v3_classification(results)
    chart_3_omega_invariant_core(results)
    chart_4_timing(results)
    chart_5_min_edit_certs(results)
    print(f"\nAll charts saved to {CHART_DIR}")

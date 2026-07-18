"""Plot experiment progress from results.tsv -> progress.png.

Shows best_seconds per experiment (in log order), highlighting kept vs
discarded/crashed runs, plus a running "best-so-far" frontier line.
Not part of the harness; just a visual aid. Regenerate with:
    uv run plot_progress.py
"""
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path="results.tsv"):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append(row)
    return rows


def main():
    rows = load()
    xs, ys, colors, statuses = [], [], [], []
    color_map = {"keep": "#2ca02c", "discard": "#d62728", "crash": "#000000"}
    for i, r in enumerate(rows):
        xs.append(i)
        try:
            y = float(r["best_seconds"])
        except ValueError:
            y = 0.0
        ys.append(y)
        statuses.append(r["status"])
        colors.append(color_map.get(r["status"], "#7f7f7f"))

    # running best (ignore crashes / 0.0)
    best_so_far = []
    cur = float("inf")
    for y, s in zip(ys, statuses):
        if s == "keep" and y > 0:
            cur = min(cur, y)
        best_so_far.append(cur if cur != float("inf") else None)

    fig, ax = plt.subplots(figsize=(11, 6))
    # plot kept points' times (skip crashes at 0 for readability of the y-axis)
    plot_x = [x for x, y in zip(xs, ys) if y > 0]
    plot_y = [y for y in ys if y > 0]
    plot_c = [c for c, y in zip(colors, ys) if y > 0]
    ax.scatter(plot_x, plot_y, c=plot_c, s=60, zorder=3, edgecolors="white", linewidths=0.5)

    fx = [x for x, b in zip(xs, best_so_far) if b is not None]
    fb = [b for b in best_so_far if b is not None]
    ax.step(fx, fb, where="post", color="#1f77b4", lw=2, zorder=2, label="best so far")

    # annotate crashes on the baseline
    for x, y, s in zip(xs, ys, statuses):
        if s == "crash":
            ax.scatter([x], [max(plot_y) if plot_y else 1], marker="x", c="black", s=40, zorder=3)

    if fb:
        ax.axhline(fb[-1], color="#1f77b4", ls="--", lw=0.8, alpha=0.5)
        ax.text(0.99, 0.1, f"current best: {fb[-1]:.4f}s", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=11, fontweight="bold",
                bbox=dict(boxstyle="round", fc="white", ec="#1f77b4"))

    # log scale so every ~1.5-4x step is visible (baseline would flatten a linear axis)
    ax.set_yscale("log")
    ax.set_xlabel("experiment #")
    ax.set_ylabel("best_seconds (lower is better, log scale)")
    speedup = f" — {plot_y[0] / fb[-1]:.0f}x faster than baseline" if fb else ""
    ax.set_title(f"primes autoresearch progress — {len(rows)} experiments{speedup}")
    ax.grid(True, which="both", alpha=0.3)

    # label each kept improvement with its description (short)
    for i, r in enumerate(rows):
        if r["status"] == "keep" and float(r["best_seconds"] or 0) > 0:
            y = float(r["best_seconds"])
            ax.annotate(f"{y:.4f}", (i, y), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=7, color="#333")

    from matplotlib.lines import Line2D
    legend_elems = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", markersize=9, label="keep"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728", markersize=9, label="discard"),
        Line2D([0], [0], marker="x", color="black", markersize=9, label="crash", lw=0),
        Line2D([0], [0], color="#1f77b4", lw=2, label="best so far"),
    ]
    ax.legend(handles=legend_elems, loc="upper right")

    fig.tight_layout()
    fig.savefig("progress.png", dpi=110)
    print(f"wrote progress.png ({len(rows)} experiments, best={fb[-1] if fb else 'n/a'})")


if __name__ == "__main__":
    main()

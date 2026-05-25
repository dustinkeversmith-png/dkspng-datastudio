"""
Advanced plot suite — all plot families.

Design rules
------------
- Outlier clipping: every distribution plot clips display to 1st-99th percentile
  and annotates how many outliers were excluded.
- Readable labels: all plots receive display_name + unit arguments.
- No raw source_key strings in plot titles — caller passes human-readable labels.
- matplotlib Agg backend throughout.
"""
from __future__ import annotations

import os
import warnings
from typing import Any

import pandas as pd

# Suppress numpy RuntimeWarnings from corrcoef/polyfit on degenerate data.
# Zero-variance series are filtered upstream, but LAPACK may still emit
# these during the correlation matrix build on borderline-constant columns.
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*invalid value.*divide.*")



# ---------------------------------------------------------------------------
# Internal setup
# ---------------------------------------------------------------------------

def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    return plt, np


def _clip_series(s: pd.Series, p_lo: float = 1.0, p_hi: float = 99.0):
    """Return (clipped_series, n_clipped, lo, hi)."""
    import numpy as np
    lo = np.percentile(s, p_lo)
    hi = np.percentile(s, p_hi)
    clipped = s[(s >= lo) & (s <= hi)]
    return clipped, len(s) - len(clipped), lo, hi


# ---------------------------------------------------------------------------
# Per-source summary (replaces individual per-variable plots)
# ---------------------------------------------------------------------------

def source_summary_plot(
    df: pd.DataFrame,
    numeric_cols: list[str],
    display_name: str,
    units: dict[str, str],
    plot_dir: str,
    tag: str = "",
) -> str:
    """One figure with one subplot per numeric variable: hist + box side-by-side."""
    plt, np = _mpl()
    cols = [c for c in numeric_cols if c in df.columns]
    if not cols:
        return ""

    n = len(cols)
    fig, axes = plt.subplots(n, 2, figsize=(12, 3 * n), squeeze=False)
    fig.suptitle(f"{display_name} — Variable Distributions", fontsize=13, fontweight="bold", y=1.01)

    for i, col in enumerate(cols):
        raw = pd.to_numeric(df[col], errors="coerce").dropna()
        if raw.empty:
            axes[i, 0].set_visible(False)
            axes[i, 1].set_visible(False)
            continue

        unit = units.get(col, "")
        xlabel = f"{col}" + (f" ({unit})" if unit else "")
        clipped, n_out, lo, hi = _clip_series(raw)

        # --- Histogram ---
        ax = axes[i, 0]
        ax.hist(clipped, bins=30, color="#5b8db8", edgecolor="white", alpha=0.85)
        ax.axvline(float(clipped.mean()), color="tomato", lw=1.5, label=f"Mean {clipped.mean():.2f}")
        ax.axvline(float(clipped.median()), color="navy", lw=1.5, linestyle="--",
                   label=f"Median {clipped.median():.2f}")
        ax.set_xlabel(xlabel); ax.set_ylabel("Count")
        ax.set_title(f"{col} — Distribution")
        ax.legend(fontsize=8)
        if n_out:
            ax.text(0.98, 0.97, f"{n_out} outliers excluded",
                    transform=ax.transAxes, ha="right", va="top", fontsize=7, color="gray")

        # Special AQI band reference
        if col == "AQI":
            _draw_aqi_bands(ax, orientation="vertical")

        # --- Box plot (clipped) ---
        ax2 = axes[i, 1]
        bp = ax2.boxplot(
            clipped.values, vert=True, patch_artist=True, widths=0.5,
            boxprops=dict(facecolor="#5b8db8", alpha=0.7),
            medianprops=dict(color="tomato", lw=2),
            whiskerprops=dict(color="#333", lw=1.2),
            capprops=dict(color="#333", lw=1.5),
            flierprops=dict(marker="o", color="#aaa", alpha=0.3, markersize=3),
            showfliers=False,
        )
        q1, q3 = float(clipped.quantile(0.25)), float(clipped.quantile(0.75))
        med = float(clipped.median())
        mean_val = float(clipped.mean())
        ax2.scatter([1], [mean_val], marker="D", color="tomato", zorder=5, s=40, label=f"Mean {mean_val:.2f} {unit}")
        ax2.set_xticks([1]); ax2.set_xticklabels([col])
        ax2.set_ylabel(xlabel)
        ax2.set_title(f"{col} — Box (IQR={q1:.2f}–{q3:.2f})")
        ax2.text(1.32, med, f"Median\n{med:.2f} {unit}", transform=ax2.get_yaxis_transform(),
                 ha="left", va="center", fontsize=7, color="tomato")
        h2, l2 = ax2.get_legend_handles_labels()
        if h2:
            ax2.legend(fontsize=7)
        if n_out:
            ax2.text(0.98, 0.97, f"{n_out} outliers hidden",
                     transform=ax2.transAxes, ha="right", va="top", fontsize=7, color="gray")

    plt.tight_layout()
    path = os.path.join(plot_dir, f"summary_{tag or 'source'}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


def _draw_aqi_bands(ax, orientation: str = "vertical"):
    """Overlay EPA AQI category bands on a histogram axis (x-axis = AQI value)."""
    bands = [
        (0,   50,  "#00e400", "Good"),
        (51,  100, "#ffff00", "Moderate"),
        (101, 150, "#ff7e00", "Unhealthy (Sensitive)"),
        (151, 200, "#ff0000", "Unhealthy"),
        (201, 300, "#8f3f97", "Very Unhealthy"),
        (301, 500, "#7e0023", "Hazardous"),
    ]
    for lo, hi, color, label in bands:
        ax.axvspan(lo, hi, alpha=0.08, color=color, label=label)


# ---------------------------------------------------------------------------
# Cross-correlation: heatmap + scatter grid
# ---------------------------------------------------------------------------

def cross_correlation_heatmap(
    corr_df: pd.DataFrame,
    title: str,
    plot_dir: str,
    tag: str = "",
) -> str:
    """Annotated correlation heatmap from a square correlation DataFrame."""
    plt, np = _mpl()
    n = len(corr_df)
    fig, ax = plt.subplots(figsize=(max(6, n * 0.9), max(5, n * 0.8)))

    mat = corr_df.values.astype(float)
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Pearson r", fraction=0.046, pad=0.04)

    ax.set_xticks(range(n)); ax.set_xticklabels(corr_df.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(n)); ax.set_yticklabels(corr_df.index, fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold")

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = mat[i, j]
            if not np.isnan(val):
                color = "white" if abs(val) > 0.6 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, color=color, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(plot_dir, f"corr_heatmap_{tag}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


def cross_variable_scatter(
    x_vals: list[float],
    y_vals: list[float],
    x_label: str,
    y_label: str,
    title: str,
    plot_dir: str,
    tag: str = "",
    pearson_r: float | None = None,
) -> str:
    """Scatter plot with regression line for two variables."""
    plt, np = _mpl()
    if len(x_vals) < 3:
        return ""

    xs = np.array(x_vals, dtype=float)
    ys = np.array(y_vals, dtype=float)
    mask = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[mask], ys[mask]
    if len(xs) < 3:
        return ""

    # Guard: skip if either axis has zero variance (constant series)
    if np.std(xs) < 1e-10 or np.std(ys) < 1e-10:
        return ""

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(xs, ys, alpha=0.45, s=18, color="#5b8db8", edgecolors="none")

    # Regression line — guarded
    try:
        coeffs = np.polyfit(xs, ys, 1)
        if np.all(np.isfinite(coeffs)):
            xfit = np.linspace(xs.min(), xs.max(), 200)
            ax.plot(xfit, np.polyval(coeffs, xfit), color="tomato", lw=1.8,
                    label=f"Fit: y = {coeffs[0]:.3f}x + {coeffs[1]:.2f}")
    except Exception:
        pass

    r_text = f"  r = {pearson_r:.3f}" if (pearson_r is not None and np.isfinite(pearson_r)) else ""
    ax.set_xlabel(x_label, fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_title(f"{title}{r_text}", fontsize=11)
    handles, _ = ax.get_legend_handles_labels()
    if handles:
        ax.legend(fontsize=8)
    plt.tight_layout()
    path = os.path.join(plot_dir, f"scatter_{tag}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


def all_pairs_scatter_grid(
    data: dict[str, pd.Series],
    display_labels: dict[str, str],
    units: dict[str, str],
    title: str,
    plot_dir: str,
    tag: str = "",
    max_pairs: int = 30,
) -> list[str]:
    """Generate a scatter + regression plot for every pair in *data*."""
    import itertools
    plt, np = _mpl()

    keys = list(data.keys())
    pairs = list(itertools.combinations(keys, 2))[:max_pairs]
    paths: list[str] = []

    for xk, yk in pairs:
        xs_raw = pd.to_numeric(data[xk], errors="coerce")
        ys_raw = pd.to_numeric(data[yk], errors="coerce")
        combined = pd.concat([xs_raw, ys_raw], axis=1).dropna()
        if len(combined) < 5:
            continue
        xs = combined.iloc[:, 0].values
        ys = combined.iloc[:, 1].values

        try:
            r = float(np.corrcoef(xs, ys)[0, 1])
        except Exception:
            r = float("nan")

        x_unit = units.get(xk.split("/")[-1], "")
        y_unit = units.get(yk.split("/")[-1], "")
        xl = display_labels.get(xk, xk) + (f" ({x_unit})" if x_unit else "")
        yl = display_labels.get(yk, yk) + (f" ({y_unit})" if y_unit else "")
        safe_tag = f"{tag}_{xk.replace('/', '_')}__vs__{yk.replace('/', '_')}"

        path = cross_variable_scatter(
            xs.tolist(), ys.tolist(), xl, yl,
            title=f"{display_labels.get(xk, xk)} vs {display_labels.get(yk, yk)}",
            plot_dir=plot_dir, tag=safe_tag, pearson_r=r,
        )
        if path:
            paths.append(path)

    return paths


# ---------------------------------------------------------------------------
# CI plot — grouped by source, normalized within-group
# ---------------------------------------------------------------------------

def confidence_interval_plot_grouped(
    records: list[dict],
    display_names: dict[str, str],
    units: dict[str, str],
    plot_dir: str,
    tag: str = "",
) -> str:
    """CI plot with one panel per source, values in natural units."""
    plt, np = _mpl()

    by_source: dict[str, list[dict]] = {}
    for r in records:
        key = r.get("source_key", "unknown")
        by_source.setdefault(key, []).append(r)

    n_sources = len(by_source)
    if n_sources == 0:
        return ""

    fig, axes = plt.subplots(1, n_sources, figsize=(5 * n_sources, 6), squeeze=False)
    fig.suptitle("95% Confidence Intervals for Variable Means", fontsize=12, fontweight="bold")

    for col_idx, (src_key, recs) in enumerate(by_source.items()):
        ax = axes[0, col_idx]
        display = display_names.get(src_key, src_key)

        # De-duplicate by target (keep bootstrap version)
        seen: dict[str, dict] = {}
        for r in recs:
            t = r.get("target") or "?"
            if t not in seen or r.get("method") == "bootstrap":
                seen[t] = r
        recs = list(seen.values())

        labels, estimates, lo_vals, hi_vals, unit_labels = [], [], [], [], []
        for r in recs:
            t = r.get("target") or "?"
            ci = r.get("confidence_interval")
            est = r.get("estimate")
            if ci is None or est is None:
                continue
            unit = units.get(t, "")
            labels.append(f"{t}" + (f"\n({unit})" if unit else ""))
            estimates.append(float(est))
            lo_vals.append(float(ci[0]))
            hi_vals.append(float(ci[1]))
            unit_labels.append(unit)

        if not labels:
            ax.set_visible(False)
            continue

        y = range(len(labels))
        ax.scatter(estimates, list(y), color="#2c7bb6", zorder=5, s=60)
        for i, (lo, hi) in enumerate(zip(lo_vals, hi_vals)):
            ax.plot([lo, hi], [i, i], color="#2c7bb6", lw=2.5, solid_capstyle="round")
            ax.annotate(f"{estimates[i]:.2f}", xy=(estimates[i], i),
                        xytext=(5, 4), textcoords="offset points", fontsize=7, color="tomato")

        ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Mean estimate (in natural units)", fontsize=9)
        ax.set_title(display, fontsize=10, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)
        ax.text(0.02, 0.01,
                "Bars show 95% CI for the population mean.\nNarrower = more certain estimate.",
                transform=ax.transAxes, fontsize=7, color="gray", va="bottom")

    plt.tight_layout()
    path = os.path.join(plot_dir, f"ci_grouped_{tag}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Sampling bias plot — readable labels + legend
# ---------------------------------------------------------------------------

def sampling_bias_plot(
    group_val: float,
    complement_val: float,
    label_group: str,
    label_complement: str,
    title: str,
    plot_dir: str,
    tag: str = "",
    unit: str = "",
    variable: str = "",
) -> str:
    plt, np = _mpl()
    fig, ax = plt.subplots(figsize=(7, 4))

    bars = ax.bar(
        [label_group, label_complement],
        [group_val, complement_val],
        color=["#e74c3c", "#3498db"], alpha=0.85, width=0.5,
        edgecolor="white", linewidth=1.2,
    )
    # Value labels on top of bars
    for bar, val in zip(bars, [group_val, complement_val]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(abs(group_val), abs(complement_val)) * 0.01,
                f"{val:.2f}{' ' + unit if unit else ''}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")

    bias = (group_val - complement_val) / (abs(complement_val) + 1e-9)
    ax.set_ylabel(f"Mean {variable}" + (f" ({unit})" if unit else ""), fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")

    direction = "higher" if bias > 0 else "lower"
    ax.text(0.98, 0.97,
            f"Group mean is {abs(bias)*100:.1f}% {direction}\nthan the rest of the dataset.",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            color="#e74c3c" if abs(bias) > 0.1 else "gray",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#ccc"))

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#e74c3c", alpha=0.85, label=f"Subgroup: {label_group}"),
        Patch(facecolor="#3498db", alpha=0.85, label=f"Complement: {label_complement}"),
    ], loc="lower right", fontsize=8)

    plt.tight_layout()
    path = os.path.join(plot_dir, f"bias_{tag}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Cluster map
# ---------------------------------------------------------------------------

def cluster_map(
    df: pd.DataFrame,
    lat_col: str,
    lon_col: str,
    labels: list[int],
    title: str,
    plot_dir: str,
    tag: str = "",
) -> str:
    plt, np = _mpl()
    fig, ax = plt.subplots(figsize=(9, 7))
    lats = pd.to_numeric(df[lat_col], errors="coerce")
    lons = pd.to_numeric(df[lon_col], errors="coerce")
    valid = lats.notna() & lons.notna()
    n = min(len(labels), valid.sum())
    sc = ax.scatter(
        lons[valid].values[:n], lats[valid].values[:n],
        c=labels[:n], cmap="tab10", alpha=0.7, s=22, edgecolors="none",
    )
    plt.colorbar(sc, ax=ax, label="Cluster ID")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(plot_dir, f"cluster_map_{tag}.png")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path

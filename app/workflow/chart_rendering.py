"""Python chart rendering for direct workflow chart definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.workflow.chart_foreach_expand import materialize_foreach_spec


def _ensure_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required for Python chart rendering.") from exc
    return plt


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name).strip("_") or "chart"


def _source_df(rows_by_source: dict[str, list[dict[str, Any]]], source_key: str | None = None) -> pd.DataFrame:
    if source_key:
        return pd.DataFrame(rows_by_source.get(source_key, []))
    rows: list[dict[str, Any]] = []
    for source_rows in rows_by_source.values():
        rows.extend(source_rows)
    return pd.DataFrame(rows)


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def _pretty_column(column: str) -> str:
    labels = {
        "metric_value": "Normalized source metric",
        "distance_km": "Distance from Klamath Falls center (km)",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "year": "Year",
        "population_per_fire_distance_km": "Population divided by fire distance",
        "metric_regression_prediction": "Regression prediction",
        "nearest_fire_km": "Nearest fire distance (km)",
        "source_label": "Source",
        "bin_label": "Frequency bin",
    }
    return labels.get(column, column.replace("_", " ").title())


def _series_label(df: pd.DataFrame, fallback: Any) -> str:
    if "source_label" in df.columns:
        values = df["source_label"].dropna().astype(str).unique()
        if len(values):
            return values[0]
    return str(fallback)


def render_chart_python(
    chart: dict[str, Any],
    rows_by_source: dict[str, list[dict[str, Any]]],
    output_path: str | Path,
) -> str:
    """Render one chart definition with matplotlib and return the output path."""
    plt = _ensure_matplotlib()
    ctype = chart.get("type")
    name = str(chart.get("name") or chart.get("name_prefix") or ctype or "chart")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(10, 6))

    if ctype == "chart_scatter":
        ax = fig.add_subplot(111)
        for series in chart.get("series", []):
            df = _source_df(rows_by_source, str(series.get("source_key", "")))
            x = _numeric(df, str(series.get("x", "")))
            y = _numeric(df, str(series.get("y", "")))
            keep = x.notna() & y.notna()
            ax.scatter(x[keep], y[keep], s=28, alpha=0.75, label=series.get("label") or _series_label(df, series.get("source_key")))
        first_series = (chart.get("series") or [{}])[0]
        ax.set_xlabel(_pretty_column(str(first_series.get("x", "x"))))
        ax.set_ylabel(_pretty_column(str(first_series.get("y", "y"))))
        ax.legend(loc="best")

    elif ctype == "chart_metric":
        ax = fig.add_subplot(111)
        for series in chart.get("series", []):
            df = _source_df(rows_by_source, str(series.get("source_key", "")))
            x = _numeric(df, str(series.get("x", "")))
            y = _numeric(df, str(series.get("y", "")))
            keep = x.notna() & y.notna()
            style = series.get("style") or {}
            ax.plot(x[keep], y[keep], marker="o", label=series.get("label") or _series_label(df, series.get("source_key")), color=style.get("color"))
        first_series = (chart.get("series") or [{}])[0]
        ax.set_xlabel(_pretty_column(str(first_series.get("x", "x"))))
        ax.set_ylabel(_pretty_column(str(first_series.get("y", "y"))))
        ax.legend(loc="best")

    elif ctype == "chart_bar":
        ax = fig.add_subplot(111)
        df = _source_df(rows_by_source, str(chart.get("source_key", "")))
        cat = str(chart.get("category", ""))
        val = str(chart.get("value", ""))
        if cat in df.columns:
            if chart.get("aggregation") == "sum":
                grouped = df.groupby(cat)[val].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
            elif chart.get("aggregation") == "mean":
                grouped = df.groupby(cat)[val].apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
            else:
                grouped = df.groupby(cat)[val].count() if val in df.columns else df.groupby(cat).size()
            grouped.sort_values(ascending=False).head(25).plot(kind="bar", ax=ax)
        ax.set_xlabel(_pretty_column(cat))
        ax.set_ylabel(_pretty_column(val) if val else "Count")

    elif ctype == "chart_heatmap":
        ax = fig.add_subplot(111)
        df = _source_df(rows_by_source, str(chart.get("source_key", "")))
        x, y, z = str(chart.get("x", "")), str(chart.get("y", "")), str(chart.get("z", ""))
        if {x, y, z}.issubset(df.columns):
            pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc="mean")
            image = ax.imshow(pivot.fillna(0).to_numpy(), aspect="auto")
            ax.set_xticks(range(len(pivot.columns)), labels=[str(c) for c in pivot.columns], rotation=45, ha="right")
            ax.set_yticks(range(len(pivot.index)), labels=[str(i) for i in pivot.index])
            fig.colorbar(image, ax=ax)

    elif ctype == "chart_correlation_matrix":
        ax = fig.add_subplot(111)
        df = _source_df(rows_by_source)
        variables = chart.get("variables") or list(df.select_dtypes(include="number").columns)
        numeric = df[[c for c in variables if c in df.columns]].apply(pd.to_numeric, errors="coerce")
        corr = numeric.corr().fillna(0)
        image = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)), labels=[_pretty_column(str(c)) for c in corr.columns], rotation=45, ha="right")
        ax.set_yticks(range(len(corr.index)), labels=[_pretty_column(str(c)) for c in corr.index])
        fig.colorbar(image, ax=ax)

    elif ctype == "chart_overlay":
        ax = fig.add_subplot(111)
        for overlay in chart.get("overlays", []):
            df = _source_df(rows_by_source, str(overlay.get("source_key", "")))
            columns = list(overlay.get("columns", []))
            for column in columns:
                y = _numeric(df, str(column)).dropna()
                ax.plot(range(len(y)), y, label=f"{overlay.get('source_key')}:{column}")
        ax.legend(loc="best")

    elif ctype == "chart_cross_pair":
        ax = fig.add_subplot(111)
        ldf = _source_df(rows_by_source, str(chart.get("left_source_key", "")))
        rdf = _source_df(rows_by_source, str(chart.get("right_source_key", "")))
        lx = _numeric(ldf, str(chart.get("left_x", "")))
        ly = _numeric(ldf, str(chart.get("left_y", "")))
        rx = _numeric(rdf, str(chart.get("right_x", "")))
        ry = _numeric(rdf, str(chart.get("right_y", "")))
        ax.scatter(lx, ly, label=str(chart.get("left_source_key")))
        ax.scatter(rx, ry, label=str(chart.get("right_source_key")))
        ax.legend(loc="best")

    elif ctype == "chart_sankey":
        ax = fig.add_subplot(111)
        df = _source_df(rows_by_source)
        if {"source", "target", "value"}.issubset(df.columns):
            grouped = df.groupby(["source", "target"])["value"].sum().reset_index()
            labels = list(dict.fromkeys([*grouped["source"].astype(str), *grouped["target"].astype(str)]))
            y_positions = {label: idx for idx, label in enumerate(labels)}
            for _, row in grouped.iterrows():
                y0 = y_positions[str(row["source"])]
                y1 = y_positions[str(row["target"])]
                ax.plot([0, 1], [y0, y1], linewidth=max(1.0, float(row["value"]) / max(grouped["value"].max(), 1) * 8), alpha=0.55)
            ax.set_yticks(range(len(labels)), labels=labels)
            ax.set_xticks([0, 1], labels=["source", "target"])
        else:
            ax.text(0.1, 0.5, "Sankey rows need source, target, value columns")

    else:
        ax = fig.add_subplot(111)
        ax.text(0.1, 0.5, f"Unsupported chart type: {ctype}")

    fig.suptitle(name)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return str(out)


def render_charts_python(
    chart_definitions: list[dict[str, Any]],
    rows_by_source: dict[str, list[dict[str, Any]]],
    output_dir: str | Path,
    *,
    fmt: str = "png",
) -> list[str]:
    """Render all chart definitions, expanding foreach definitions first."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for chart in chart_definitions:
        charts = materialize_foreach_spec(chart) if chart.get("type") == "chart_foreach" else [chart]
        for concrete in charts:
            name = str(concrete.get("name") or concrete.get("name_prefix") or concrete.get("type") or "chart")
            saved.append(render_chart_python(concrete, rows_by_source, out_dir / f"{_safe_name(name)}.{fmt}"))
    return saved

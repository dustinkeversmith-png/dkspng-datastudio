"""
Render chart images directly from stored chart definitions.

This keeps script output aligned with the same chart specs created via `.charts.*(...)`.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from app.source_registry import get_source
from app.workflow.chart_foreach_expand import materialize_foreach_spec


def _ensure_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "matplotlib is required for chart image exports. Install with: pip install matplotlib"
        ) from exc
    return plt


def _fetch_csv(url: str, *, timeout_s: float = 25.0) -> pd.DataFrame:
    resp = requests.get(url, timeout=timeout_s)
    resp.raise_for_status()
    text = resp.text
    if text.lstrip().startswith("{"):
        raise RuntimeError(f"CSV endpoint returned JSON payload for {url}: {text[:180]}")
    return pd.read_csv(StringIO(text), low_memory=False)


def _fetch_arcgis(url: str, *, limit: int = 4000, timeout_s: float = 25.0) -> pd.DataFrame:
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
    }
    resp = requests.get(url, params=params, timeout=timeout_s)
    resp.raise_for_status()
    payload = resp.json()
    features = payload.get("features", [])
    rows = [f.get("attributes", {}) for f in features][:limit]
    return pd.DataFrame(rows)


def _load_source_df(source_key: str, cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if source_key in cache:
        return cache[source_key]
    src = get_source(source_key)
    if src.connector_type in ("csv", "web"):
        df = _fetch_csv(src.source_url)
    elif src.connector_type == "arcgis_rest":
        df = _fetch_arcgis(src.source_url)
    else:
        raise ValueError(f"Unsupported connector for chart export: {src.connector_type}")
    cache[source_key] = df
    return df


def _series_from_df(df: pd.DataFrame, x_col: str, y_col: str, filter_slice: dict[str, Any] | None = None) -> tuple[pd.Series, pd.Series]:
    subset = df
    if filter_slice:
        if "year_min" in filter_slice and "year" in subset.columns:
            y = pd.to_numeric(subset["year"], errors="coerce")
            subset = subset[y >= int(filter_slice["year_min"])]
        if "year_max" in filter_slice and "year" in subset.columns:
            y = pd.to_numeric(subset["year"], errors="coerce")
            subset = subset[y <= int(filter_slice["year_max"])]
    if x_col not in subset.columns or y_col not in subset.columns:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    x = pd.to_numeric(subset[x_col], errors="coerce")
    y = pd.to_numeric(subset[y_col], errors="coerce")
    keep = x.notna() & y.notna()
    return x[keep], y[keep]


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name).strip("_") or "chart"


def render_defined_charts_to_images(
    chart_definitions: list[dict[str, Any]],
    output_dir: str | Path,
    *,
    fmt: str = "png",
) -> list[str]:
    """
    Render chart images from chart definitions.

    Supports: chart_scatter, chart_bar, chart_metric, chart_foreach (expanded).
    """
    plt = _ensure_matplotlib()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_cache: dict[str, pd.DataFrame] = {}
    saved: list[str] = []

    def render_one(chart: dict[str, Any]) -> None:
        ctype = chart.get("type")
        name = str(chart.get("name") or chart.get("name_prefix") or ctype or "chart")
        out_path = out_dir / f"{_safe_name(name)}.{fmt}"

        if ctype == "chart_scatter":
            fig = plt.figure(figsize=(10, 6))
            for s in chart.get("series", []):
                sk = str(s.get("source_key", ""))
                if not sk:
                    continue
                df = _load_source_df(sk, source_cache)
                x, y = _series_from_df(df, str(s.get("x", "")), str(s.get("y", "")))
                if len(x) == 0:
                    continue
                plt.scatter(x, y, s=8, alpha=0.35, label=s.get("label") or sk)
            plt.title(name)
            plt.xlabel("X")
            plt.ylabel("Y")
            if len(chart.get("series", [])) > 1:
                plt.legend()
            plt.tight_layout()
            fig.savefig(out_path, dpi=160)
            plt.close(fig)
            saved.append(str(out_path))
            return

        if ctype == "chart_bar":
            sk = str(chart.get("source_key", ""))
            if not sk:
                return
            df = _load_source_df(sk, source_cache)
            cat = str(chart.get("category", ""))
            val = str(chart.get("value", ""))
            if cat not in df.columns or val not in df.columns:
                return
            g = (
                df[[cat, val]]
                .dropna()
                .assign(_v=pd.to_numeric(df[val], errors="coerce"))
                .dropna()
                .groupby(cat)["_v"]
                .count()
                .sort_values(ascending=False)
                .head(30)
            )
            fig = plt.figure(figsize=(11, 6))
            g.plot(kind="bar", color="#2b6cb0")
            plt.title(name)
            plt.xlabel(cat)
            plt.ylabel("Count")
            plt.tight_layout()
            fig.savefig(out_path, dpi=160)
            plt.close(fig)
            saved.append(str(out_path))
            return

        if ctype == "chart_metric":
            fig = plt.figure(figsize=(10, 6))
            for s in chart.get("series", []):
                sk = str(s.get("source_key", ""))
                if not sk:
                    continue
                df = _load_source_df(sk, source_cache)
                x, y = _series_from_df(
                    df,
                    str(s.get("x", "")),
                    str(s.get("y", "")),
                    filter_slice=s.get("filter_slice"),
                )
                if len(x) == 0:
                    continue
                label = s.get("label") or sk
                style = s.get("style") or {}
                plt.plot(x, y, label=label, color=style.get("color"))
            plt.title(name)
            plt.xlabel("X")
            plt.ylabel("Y")
            handles, labels = plt.gca().get_legend_handles_labels()
            if handles and labels:
                plt.legend()
            plt.tight_layout()
            fig.savefig(out_path, dpi=160)
            plt.close(fig)
            saved.append(str(out_path))
            return

    for raw in chart_definitions:
        if raw.get("type") == "chart_foreach":
            for expanded in materialize_foreach_spec(raw):
                render_one(expanded)
            continue
        render_one(raw)

    return saved


"""
Simple image export helpers for chart specs and analysis summaries.

Exports SVG files so saving "as picture" works without extra dependencies.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


def _save_svg(path: str | Path, svg_body: str) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg_body, encoding="utf-8")
    return str(out)


def export_chart_spec_svg(
    chart: dict[str, Any],
    output_path: str | Path,
    *,
    width: int = 1200,
    height: int = 700,
) -> str:
    """Render a compact picture of chart metadata."""
    name = escape(str(chart.get("name", "Untitled chart")))
    ctype = escape(str(chart.get("type", "unknown")))
    lines = [f"Type: {ctype}"]
    if "series" in chart and isinstance(chart["series"], list):
        lines.append(f"Series: {len(chart['series'])}")
        for i, s in enumerate(chart["series"][:8], start=1):
            sk = escape(str(s.get("source_key", "?")))
            x = escape(str(s.get("x", "?")))
            y = escape(str(s.get("y", "?")))
            lines.append(f"{i}. {sk}: {y} vs {x}")
    elif ctype == "chart_bar":
        lines.append(f"Source: {escape(str(chart.get('source_key', '?')))}")
        lines.append(f"Category: {escape(str(chart.get('category', '?')))}")
        lines.append(f"Value: {escape(str(chart.get('value', '?')))}")

    y = 140
    text_nodes = []
    for line in lines:
        text_nodes.append(
            f'<text x="70" y="{y}" font-size="28" fill="#243447" font-family="Arial">{escape(line)}</text>'
        )
        y += 42

    svg = (
        _svg_header(width, height)
        + '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc"/>'
        + '<rect x="40" y="40" width="1120" height="620" rx="18" fill="#ffffff" stroke="#d0d7de"/>'
        + f'<text x="70" y="95" font-size="36" fill="#111827" font-family="Arial" font-weight="bold">{name}</text>'
        + "".join(text_nodes)
        + "</svg>"
    )
    return _save_svg(output_path, svg)


def export_analysis_svg(
    title: str,
    lines: list[str],
    output_path: str | Path,
    *,
    width: int = 1200,
    height: int = 700,
) -> str:
    """Save analysis notes as an image-like report card (SVG)."""
    y = 140
    text_nodes = []
    for line in lines[:14]:
        text_nodes.append(
            f'<text x="70" y="{y}" font-size="26" fill="#1f2937" font-family="Arial">- {escape(line)}</text>'
        )
        y += 38

    svg = (
        _svg_header(width, height)
        + '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc"/>'
        + '<rect x="40" y="40" width="1120" height="620" rx="18" fill="#ffffff" stroke="#d0d7de"/>'
        + f'<text x="70" y="95" font-size="36" fill="#111827" font-family="Arial" font-weight="bold">{escape(title)}</text>'
        + "".join(text_nodes)
        + "</svg>"
    )
    return _save_svg(output_path, svg)

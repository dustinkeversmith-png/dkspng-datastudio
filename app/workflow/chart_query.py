"""
Decoupled chart construction: combine metric series, optional per-trace styles, and export layout.

Used by :class:`app.workflow.source_binding.Charts` and :class:`SessionPipeline`.
"""

from __future__ import annotations

from typing import Any

from app.chart_specs import MetricChartSpec, MetricSeries, TraceStyle


def build_metric_chart(
    name: str,
    series: list[dict[str, Any]],
    *,
    layout: dict[str, Any] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Validate and serialize a metric chart from loose series dicts."""
    parsed = []
    for row in series:
        style = row.get("style")
        ts: TraceStyle | None = None
        if style is None:
            ts = None
        elif isinstance(style, TraceStyle):
            ts = style
        else:
            ts = TraceStyle.model_validate(style)
        fs = row.get("filter_slice")
        parsed.append(
            MetricSeries(
                source_key=row["source_key"],
                x=row["x"],
                y=row["y"],
                label=row.get("label"),
                style=ts,
                query_ref=row.get("query_ref"),
                filter_slice=dict(fs) if isinstance(fs, dict) else fs,
            )
        )
    spec = MetricChartSpec(name=name, series=parsed, layout=dict(layout or {}), notes=notes)
    return spec.model_dump()

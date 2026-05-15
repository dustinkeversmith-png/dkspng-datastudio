"""
Expand declarative foreach/grid intents into concrete chart specs (scatter, bar, metric, ranges).

Separated from session persistence so UI and CLI can reuse the same expansion rules.
"""

from __future__ import annotations

from typing import Any, Literal, Sequence

from app.chart_specs import BarChartSpec, ForeachChartSpec, ScatterChartSpec, ScatterSeries


def expand_pair_grid(
    source_key: str,
    x_columns: list[str],
    y_columns: list[str],
    *,
    kinds: Sequence[Literal["scatter", "bar"]] = ("scatter", "bar"),
    name_prefix: str = "grid",
    skip_identity: bool = True,
) -> list[dict[str, Any]]:
    """
    Cartesian product of ``x_columns × y_columns × kinds``.

    Bar charts use ``category=x``, ``value=y`` (aggregate semantics stay client-side).
    """
    out: list[dict[str, Any]] = []
    for kind in kinds:
        for xc in x_columns:
            for yc in y_columns:
                if skip_identity and xc == yc:
                    continue
                safe = f"{name_prefix}_{kind}_{xc}_{yc}".replace(" ", "_")
                if kind == "scatter":
                    spec = ScatterChartSpec(
                        name=safe,
                        series=[ScatterSeries(source_key=source_key, x=xc, y=yc)],
                    )
                    out.append(spec.model_dump())
                else:
                    spec = BarChartSpec(
                        name=safe,
                        source_key=source_key,
                        category=xc,
                        value=yc,
                        aggregation="count",
                    )
                    out.append(spec.model_dump())
    return out


def expand_metric_ranges(
    source_key: str,
    x: str,
    y: str,
    year_ranges: list[tuple[int, int]],
    *,
    base_name: str = "slice",
) -> list[dict[str, Any]]:
    """Emit one :class:`MetricChartSpec`-compatible dict per year window with ``filter_slice`` hints."""
    from app.workflow.chart_query import build_metric_chart

    charts: list[dict[str, Any]] = []
    for lo, hi in year_ranges:
        label = f"{base_name}_{lo}_{hi}"
        charts.append(
            build_metric_chart(
                label,
                [
                    {
                        "source_key": source_key,
                        "x": x,
                        "y": y,
                        "label": label,
                        "filter_slice": {"year_min": lo, "year_max": hi},
                    }
                ],
                notes=f"Year slice [{lo}, {hi}] — apply when resolving rows for this trace.",
            )
        )
    return charts


def materialize_foreach_spec(spec: ForeachChartSpec | dict[str, Any]) -> list[dict[str, Any]]:
    """Turn a stored :class:`ForeachChartSpec` into concrete charts."""
    if isinstance(spec, dict):
        spec = ForeachChartSpec.model_validate(spec)
    return expand_pair_grid(
        spec.source_key,
        spec.x_columns,
        spec.y_columns,
        kinds=tuple(spec.chart_kinds),
        name_prefix=spec.name_prefix,
    )

"""Time-series oriented chart hints (year index, trends)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.chart_specs import BarChartSpec, ScatterChartSpec, ScatterSeries

if TYPE_CHECKING:
    from app.workflow.session_pipeline import SessionPipeline


class SeriesSolver:
    """Convenience constructors for common ``year`` / metric layouts."""

    def __init__(self, pipeline: SessionPipeline) -> None:
        self._pipeline = pipeline

    def line_vs_year(self, name: str, source_key: str, y_metric: str, x_year: str = "year") -> SessionPipeline:
        spec = ScatterChartSpec(
            name=name,
            series=[ScatterSeries(source_key=source_key, x=x_year, y=y_metric)],
        )
        return self._pipeline.push_chart_dict(spec.model_dump())

    def bar_by_year(self, name: str, source_key: str, category: str = "year", value: str = "metric_value") -> SessionPipeline:
        spec = BarChartSpec(
            name=name,
            source_key=source_key,
            category=category,
            value=value,
            aggregation="sum",
        )
        return self._pipeline.push_chart_dict(spec.model_dump())

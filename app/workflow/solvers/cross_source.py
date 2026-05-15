"""Cross-dataset / cross-variable pairing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.chart_specs import CrossPairChartSpec, ScatterChartSpec, ScatterSeries
from app.workflow.chart_query import build_metric_chart

if TYPE_CHECKING:
    from app.workflow.session_pipeline import SessionPipeline


class CrossSourceSolver:
    """
    Build comparison charts that reference two source keys (four chosen columns).

    Execution policy (join / align rows) stays client-side; specs are declarative.
    """

    def __init__(self, pipeline: SessionPipeline) -> None:
        self._pipeline = pipeline

    def scatter_pair(
        self,
        name: str,
        left: tuple[str, str, str],
        right: tuple[str, str, str],
    ) -> SessionPipeline:
        """``(source_key, x, y)`` for each side."""
        lk, lx, ly = left
        rk, rx, ry = right
        spec = ScatterChartSpec(
            name=name,
            series=[
                ScatterSeries(source_key=lk, x=lx, y=ly),
                ScatterSeries(source_key=rk, x=rx, y=ry),
            ],
        )
        return self._pipeline.push_chart_dict(spec.model_dump())

    def cross_four(
        self,
        name: str,
        left_source_key: str,
        right_source_key: str,
        left_x: str,
        left_y: str,
        right_x: str,
        right_y: str,
    ) -> SessionPipeline:
        spec = CrossPairChartSpec(
            name=name,
            left_source_key=left_source_key,
            right_source_key=right_source_key,
            left_x=left_x,
            left_y=left_y,
            right_x=right_x,
            right_y=right_y,
        )
        return self._pipeline.push_chart_dict(spec.model_dump())

    def metric_pair(
        self,
        name: str,
        left: tuple[str, str, str],
        right: tuple[str, str, str],
        *,
        left_style: dict | None = None,
        right_style: dict | None = None,
        layout: dict | None = None,
    ) -> SessionPipeline:
        """Two-trace metric chart with optional colors/names (contrasts with basic :meth:`scatter_pair`)."""
        lk, lx, ly = left
        rk, rx, ry = right
        a: dict = {"source_key": lk, "x": lx, "y": ly, "label": lk}
        b: dict = {"source_key": rk, "x": rx, "y": ry, "label": rk}
        if left_style:
            a["style"] = left_style
        if right_style:
            b["style"] = right_style
        return self._pipeline.push_chart_dict(build_metric_chart(name, [a, b], layout=layout))

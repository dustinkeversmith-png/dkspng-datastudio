"""Declarative chart definitions for visualization sessions (stored server-side, consumed by UI or exports)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_validator


class ScatterSeries(BaseModel):
    source_key: str
    x: str
    y: str
    label: str | None = None


class TraceStyle(BaseModel):
    """Per-trace presentation hints for renderers (Plotly, Vega, export)."""

    color: str | None = None
    marker_symbol: str | None = None
    line_dash: str | None = None
    line_width: float | None = None
    opacity: float | None = None


class MetricSeries(BaseModel):
    """One plotted trace with optional styling — supports multi-source overlays."""

    source_key: str
    x: str
    y: str
    label: str | None = None
    style: TraceStyle | None = None
    #: Optional named slice of query profile keys to apply when resolving this trace only (future).
    query_ref: str | None = None
    #: Row-filter hints for render-time slicing (e.g. ``year_min`` / ``year_max`` windows).
    filter_slice: dict[str, Any] | None = None


class MetricChartSpec(BaseModel):
    """
    Primary chart constructor for combined metrics: multiple sources/columns, layout, styling.

    Prefer this over bare scatter specs when you need colors, legend names, or export layout.
    """

    type: Literal["chart_metric"] = "chart_metric"
    name: str
    series: list[MetricSeries]
    layout: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class ScatterChartSpec(BaseModel):
    type: Literal["chart_scatter"] = "chart_scatter"
    name: str
    series: list[ScatterSeries]


class OverlaySeries(BaseModel):
    source_key: str
    columns: tuple[str, ...]


class MultiOverlayChartSpec(BaseModel):
    """Multiple traces sharing axes (e.g. paired A/B lines)."""

    type: Literal["chart_overlay"] = "chart_overlay"
    name: str
    overlays: list[OverlaySeries]


class SankeyChartSpec(BaseModel):
    type: Literal["chart_sankey"] = "chart_sankey"
    name: str
    source_keys: list[str] = Field(default_factory=list)
    notes: str | None = None


class HeatmapChartSpec(BaseModel):
    type: Literal["chart_heatmap"] = "chart_heatmap"
    name: str
    source_key: str
    x: str
    y: str
    z: str


class CorrelationMatrixSpec(BaseModel):
    type: Literal["chart_correlation_matrix"] = "chart_correlation_matrix"
    name: str
    source_keys: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)


class BarChartSpec(BaseModel):
    """Category axis + numeric measure (client aggregates rows per category when needed)."""

    type: Literal["chart_bar"] = "chart_bar"
    name: str
    source_key: str
    category: str
    value: str
    aggregation: Literal["sum", "count", "mean", "none"] = "count"


class ForeachChartSpec(BaseModel):
    """Expand into multiple scatter/bar specs over column grids (UI/materializer consumes)."""

    type: Literal["chart_foreach"] = "chart_foreach"
    name_prefix: str
    source_key: str
    x_columns: list[str]
    y_columns: list[str]
    chart_kinds: list[Literal["scatter", "bar"]] = Field(default_factory=lambda: ["scatter"])

    @model_validator(mode="before")
    @classmethod
    def _legacy_single_chart_kind(cls, data: Any) -> Any:
        if isinstance(data, dict) and "chart_kind" in data and "chart_kinds" not in data:
            data = dict(data)
            data["chart_kinds"] = [data.pop("chart_kind")]
        return data


class CrossPairChartSpec(BaseModel):
    """Two-variable comparison across two feeds (coordinates matched by client/join policy)."""

    type: Literal["chart_cross_pair"] = "chart_cross_pair"
    name: str
    left_source_key: str
    right_source_key: str
    left_x: str
    left_y: str
    right_x: str
    right_y: str


ChartDefinition = (
    ScatterChartSpec
    | MetricChartSpec
    | MultiOverlayChartSpec
    | SankeyChartSpec
    | HeatmapChartSpec
    | CorrelationMatrixSpec
    | BarChartSpec
    | ForeachChartSpec
    | CrossPairChartSpec
)

_chart_adapter = TypeAdapter(ChartDefinition)


class SaveSnapshotSpec(BaseModel):
    """Recorded bundle for export or reproducibility."""

    type: Literal["save_snapshot"] = "save_snapshot"
    name: str
    include_buffer: bool = True
    include_charts: bool = True
    include_pipeline: bool = True
    notes: str | None = None


def validate_chart_definition(raw: dict[str, Any]) -> ChartDefinition:
    return _chart_adapter.validate_python(raw)


def validate_save_snapshot(raw: dict[str, Any]) -> SaveSnapshotSpec:
    return SaveSnapshotSpec.model_validate(raw)

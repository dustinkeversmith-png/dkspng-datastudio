"""
Class-based workflow for visualization sessions: sources, buffer commands,
chart specs, and named saves — mirrors the HTTP API without requiring FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from app.chart_specs import (
    BarChartSpec,
    CorrelationMatrixSpec,
    ForeachChartSpec,
    HeatmapChartSpec,
    MultiOverlayChartSpec,
    OverlaySeries,
    SankeyChartSpec,
    SaveSnapshotSpec,
    ScatterChartSpec,
    ScatterSeries,
    validate_chart_definition,
    validate_save_snapshot,
)
from app.workflow.chart_foreach_expand import expand_metric_ranges, expand_pair_grid
from app.workflow.definition_chart_export import render_defined_charts_to_images
from app.workflow.picture_export import export_analysis_svg, export_chart_spec_svg
from app.workflow.chart_query import build_metric_chart
from app.schemas import SourceDefinition
from app.source_registry import add_or_update_source
from app.visualization_session import (
    VisualizationSession,
    add_dataset,
    append_buffer_command,
    append_chart_definition,
    append_saved_snapshot,
    clear_buffer,
    create_session,
    delete_session,
    get_session,
    merge_source_query_profile,
)


def _slug_dataset_id(source_key: str) -> str:
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in source_key)
    return f"ds_{safe}"[:64]


@dataclass
class ColumnResolver:
    """Resolve positional column picks (0-based or string digits) to column names."""

    names: list[str] = field(default_factory=list)

    def set_columns(self, names: Sequence[str]) -> None:
        self.names = list(names)

    def resolve(self, token: str | int) -> str:
        if isinstance(token, int):
            return self.names[token]
        s = str(token).strip()
        if s.isdigit():
            return self.names[int(s)]
        return s

    def resolve_all(self, tokens: Iterable[str | int]) -> list[str]:
        return [self.resolve(t) for t in tokens]


class SessionPipeline:
    """
    Fluent builder tied to one visualization session.

    - ``new_session()`` creates a fresh session and optionally removes the previous one from the server registry.
    - ``add_source`` registers a URL-backed source (default ``connector_type="web"`` → CSV/HTTP fetch).
    - Buffer commands stack until ``apply_buffer`` (via API) or you append explicitly.
    """

    def __init__(
        self,
        *,
        session_id: str | None = None,
        column_resolver: ColumnResolver | None = None,
        discard_previous_on_new: bool = True,
    ) -> None:
        self._session_id = session_id
        self._discard_previous = discard_previous_on_new
        self.columns = column_resolver or ColumnResolver()

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def bind_session(self, session_id: str) -> SessionPipeline:
        self._session_id = session_id
        return self

    def new_session(self, label: str | None = None) -> VisualizationSession:
        if self._discard_previous and self._session_id:
            delete_session(self._session_id)
        created = create_session(label)
        self._session_id = created.session_id
        return created

    def add_source(
        self,
        source_key: str,
        url: str,
        *,
        display_name: str | None = None,
        category: str = "custom_web",
        connector_type: str = "web",
        dataset_id: str | None = None,
        notes: str | None = None,
    ) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("Call new_session() or bind_session() before add_source.")
        src = SourceDefinition(
            source_key=source_key,
            display_name=display_name or source_key,
            category=category,
            connector_type=connector_type,
            source_url=url,
            notes=notes,
        )
        add_or_update_source(src)
        did = dataset_id or _slug_dataset_id(source_key)
        add_dataset(self._session_id, did, source_key)
        return self

    def reference(self, source_key: str, *, mode: str = "union") -> SessionPipeline:
        """Restrict subsequent buffer transforms to rows tagged with this ``source_key``."""
        return self._push_buffer(
            {"type": "reference_scope", "source_keys": [source_key], "mode": mode}
        )

    def reference_many(self, *source_keys: str, mode: str = "union") -> SessionPipeline:
        return self._push_buffer({"type": "reference_scope", "source_keys": list(source_keys), "mode": mode})

    def exclude_columns(self, *columns: str | int, dataset_id: str | None = None) -> SessionPipeline:
        resolved = self.columns.resolve_all(columns)
        payload: dict[str, Any] = {"type": "exclude_columns", "columns": resolved}
        if dataset_id:
            payload["dataset_id"] = dataset_id
        return self._push_buffer(payload)

    def exclude_rows(self, *indices: int, dataset_id: str | None = None) -> SessionPipeline:
        payload: dict[str, Any] = {"type": "exclude_rows", "indices": list(indices)}
        if dataset_id:
            payload["dataset_id"] = dataset_id
        return self._push_buffer(payload)

    def stack_columns(
        self,
        id_vars: list[str],
        measure_vars: list[str],
        *,
        var_name: str = "variable",
        value_name: str = "value",
        dataset_id: str | None = None,
    ) -> SessionPipeline:
        payload: dict[str, Any] = {
            "type": "stack_columns",
            "id_vars": id_vars,
            "measure_vars": measure_vars,
            "var_name": var_name,
            "value_name": value_name,
        }
        if dataset_id:
            payload["dataset_id"] = dataset_id
        return self._push_buffer(payload)

    def rename_columns(self, mapping: dict[str, str], dataset_id: str | None = None) -> SessionPipeline:
        payload: dict[str, Any] = {"type": "rename_columns", "mapping": mapping}
        if dataset_id:
            payload["dataset_id"] = dataset_id
        return self._push_buffer(payload)

    def scatter_chart(self, name: str, series: list[tuple[str, str, str]]) -> SessionPipeline:
        """Each tuple is (source_key, x_column, y_column)."""
        spec = ScatterChartSpec(
            name=name,
            series=[ScatterSeries(source_key=s[0], x=s[1], y=s[2]) for s in series],
        )
        return self._push_chart(spec.model_dump())

    def overlay_chart(self, name: str, overlays: list[tuple[str, Sequence[str]]]) -> SessionPipeline:
        """Overlays: (source_key, (col_a, col_b, ...))."""
        spec = MultiOverlayChartSpec(
            name=name,
            overlays=[OverlaySeries(source_key=k, columns=tuple(v)) for k, v in overlays],
        )
        return self._push_chart(spec.model_dump())

    def sankey_chart(self, name: str, source_keys: list[str] | None = None) -> SessionPipeline:
        spec = SankeyChartSpec(name=name, source_keys=list(source_keys or []))
        return self._push_chart(spec.model_dump())

    def heatmap_chart(self, name: str, source_key: str, x: str, y: str, z: str) -> SessionPipeline:
        spec = HeatmapChartSpec(name=name, source_key=source_key, x=x, y=y, z=z)
        return self._push_chart(spec.model_dump())

    def correlation_matrix_chart(
        self,
        name: str,
        *,
        source_keys: list[str] | None = None,
        variables: list[str] | None = None,
    ) -> SessionPipeline:
        spec = CorrelationMatrixSpec(
            name=name,
            source_keys=list(source_keys or []),
            variables=list(variables or []),
        )
        return self._push_chart(spec.model_dump())

    def bar_chart(
        self,
        name: str,
        source_key: str,
        category: str,
        value: str,
        *,
        aggregation: str = "count",
    ) -> SessionPipeline:
        spec = BarChartSpec(
            name=name,
            source_key=source_key,
            category=category,
            value=value,
            aggregation=aggregation,  # type: ignore[arg-type]
        )
        return self._push_chart(spec.model_dump())

    def foreach_charts(
        self,
        name_prefix: str,
        source_key: str,
        x_columns: list[str],
        y_columns: list[str],
        *,
        chart_kinds: list[str] | None = None,
        chart_kind: str | None = None,
    ) -> SessionPipeline:
        kinds_list: list[str]
        if chart_kinds is not None:
            kinds_list = list(chart_kinds)
        elif chart_kind is not None:
            kinds_list = [chart_kind]
        else:
            kinds_list = ["scatter"]
        spec = ForeachChartSpec(
            name_prefix=name_prefix,
            source_key=source_key,
            x_columns=x_columns,
            y_columns=y_columns,
            chart_kinds=kinds_list,  # type: ignore[arg-type]
        )
        return self._push_chart(spec.model_dump())

    def bulk_charts(self, charts: list[dict[str, Any]]) -> SessionPipeline:
        """Push many validated chart definitions (e.g. from :mod:`chart_foreach_expand`)."""
        for ch in charts:
            self.push_chart_dict(ch)
        return self

    def foreach_expand_pairs(
        self,
        source_key: str,
        x_columns: list[str],
        y_columns: list[str],
        *,
        kinds: tuple[str, ...] = ("scatter", "bar"),
        name_prefix: str = "grid",
    ) -> SessionPipeline:
        """Emit every combination of kinds × columns as separate charts."""
        expanded = expand_pair_grid(
            source_key,
            x_columns,
            y_columns,
            kinds=kinds,  # type: ignore[arg-type]
            name_prefix=name_prefix,
        )
        return self.bulk_charts(expanded)

    def foreach_year_metric_slices(
        self,
        source_key: str,
        x: str,
        y: str,
        year_ranges: list[tuple[int, int]],
        *,
        base_name: str = "year_slice",
    ) -> SessionPipeline:
        """One metric chart per ``(year_min, year_max)`` window with ``filter_slice`` metadata."""
        return self.bulk_charts(expand_metric_ranges(source_key, x, y, year_ranges, base_name=base_name))

    def metric_chart(
        self,
        name: str,
        series: list[dict[str, Any]],
        *,
        layout: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> SessionPipeline:
        """Multi-trace chart with per-series styling (see :class:`app.chart_specs.MetricChartSpec`)."""
        return self.push_chart_dict(build_metric_chart(name, series, layout=layout, notes=notes))

    def push_chart_dict(self, chart: dict[str, Any]) -> SessionPipeline:
        """Public hook for solvers / DSL layers."""
        return self._push_chart(chart)

    def apply_source_query_profile(self, source_key: str, profile: dict[str, Any]) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("No session.")
        merge_source_query_profile(self._session_id, source_key, profile)
        return self

    def save_snapshot(
        self,
        name: str,
        *,
        include_buffer: bool = True,
        include_charts: bool = True,
        include_pipeline: bool = True,
        notes: str | None = None,
    ) -> SessionPipeline:
        spec = SaveSnapshotSpec(
            name=name,
            include_buffer=include_buffer,
            include_charts=include_charts,
            include_pipeline=include_pipeline,
            notes=notes,
        )
        return self._push_save(spec.model_dump())

    def save_chart_picture(
        self,
        output_path: str,
        *,
        chart_name: str | None = None,
        chart_index: int = -1,
        width: int = 1200,
        height: int = 700,
    ) -> str:
        """
        Save one chart spec as a picture (SVG).

        If ``chart_name`` is provided, the first matching chart is exported.
        Otherwise ``chart_index`` (default latest) is used.
        """
        if not self._session_id:
            raise RuntimeError("No session.")
        session = get_session(self._session_id)
        charts = list(session.chart_definitions)
        if not charts:
            raise ValueError("No charts found in this session.")

        chosen: dict[str, Any] | None = None
        if chart_name:
            for ch in charts:
                if str(ch.get("name", "")).strip().lower() == chart_name.strip().lower():
                    chosen = ch
                    break
            if chosen is None:
                raise ValueError(f"Chart not found by name: {chart_name}")
        else:
            chosen = charts[chart_index]

        return export_chart_spec_svg(chosen, output_path, width=width, height=height)

    def save_analysis_picture(
        self,
        title: str,
        lines: list[str],
        output_path: str,
        *,
        width: int = 1200,
        height: int = 700,
    ) -> str:
        """Save analysis notes as a picture (SVG)."""
        return export_analysis_svg(title, lines, output_path, width=width, height=height)

    def save_defined_chart_images(self, output_dir: str, *, fmt: str = "png") -> list[str]:
        """
        Render and save actual chart images directly from this session's chart definitions.

        This consumes `.charts.*(...)` definitions (including `chart_foreach`) and writes image files.
        """
        if not self._session_id:
            raise RuntimeError("No session.")
        session = get_session(self._session_id)
        return render_defined_charts_to_images(session.chart_definitions, output_dir, fmt=fmt)

    def clear_command_buffer(self) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("No session.")
        clear_buffer(self._session_id)
        return self

    def _push_buffer(self, command: dict[str, Any]) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("No session.")
        from app.data_manipulation import validate_pipeline_steps

        validate_pipeline_steps([command])
        append_buffer_command(self._session_id, command)
        return self

    def _push_chart(self, chart: dict[str, Any]) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("No session.")
        validate_chart_definition(chart)
        append_chart_definition(self._session_id, chart)
        return self

    def _push_save(self, snap: dict[str, Any]) -> SessionPipeline:
        if not self._session_id:
            raise RuntimeError("No session.")
        validate_save_snapshot(snap)
        bundle = self.materialize_snapshot(snap)
        append_saved_snapshot(self._session_id, bundle)
        return self

    def materialize_snapshot(self, snap: dict[str, Any]) -> dict[str, Any]:
        """Attach live session state so exports are self-describing."""
        if not self._session_id:
            return snap
        session = get_session(self._session_id)
        out = dict(snap)
        if snap.get("include_buffer", True):
            out["buffer"] = list(session.command_buffer)
        if snap.get("include_charts", True):
            out["charts"] = list(session.chart_definitions)
        if snap.get("include_pipeline", True):
            out["pipeline"] = list(session.pipeline)
        out["datasets"] = {did: b.source_key for did, b in session.datasets.items()}
        out["query_profile"] = dict(session.query_profile)
        out["source_query_profiles"] = {k: dict(v) for k, v in session.source_query_profiles.items()}
        out["session_id"] = session.session_id
        return out

"""
High-level ``Source`` + ``Charts`` façade: geo/text/year filters and chart helpers.

Designed for a stable surface (method chaining) with injectable resolvers for tests
and future command-parser backends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.querying import query_observations
from app.chart_specs import (
    BarChartSpec,
    CorrelationMatrixSpec,
    CrossPairChartSpec,
    ForeachChartSpec,
    HeatmapChartSpec,
    MultiOverlayChartSpec,
    OverlaySeries,
    SankeyChartSpec,
    ScatterChartSpec,
    ScatterSeries,
    validate_chart_definition,
)
from app.schemas import SourceDefinition
from app.session_query_filters import effective_observation_filters
from app.source_registry import add_or_update_source, get_source
from app.workflow.chart_query import build_metric_chart
from app.workflow.chart_foreach_expand import expand_metric_ranges, expand_pair_grid
from app.workflow.chart_rendering import render_charts_python
from app.workflow.picture_export import export_chart_spec_svg
from app.workflow.query.column_resolver import FuzzyColumnResolver
from app.workflow.query.geo_resolver import GeoQueryResolver
from app.workflow.query.gis_resolver import GisQueryResolver
from app.workflow.query.range_resolver import RangeQueryResolver
from app.workflow.solvers.cross_source import CrossSourceSolver
from app.workflow.solvers.series import SeriesSolver

if TYPE_CHECKING:
    from app.workflow.session_pipeline import SessionPipeline


def source(
    key: str,
    url: str,
    *,
    pipeline: SessionPipeline | None = None,
    geo: GeoQueryResolver | None = None,
    column_hints: list[str] | None = None,
    connector_type: str | None = None,
) -> Source:
    return Source(
        key,
        url,
        pipeline=pipeline,
        geo=geo,
        column_hints=column_hints or [],
        connector_type=connector_type or _infer_connector_type(url),
    )


def charts() -> Charts:
    """Create a standalone chart builder."""
    return Charts()


def analysis_tools() -> AnalysisTools:
    """Create direct analysis helpers that operate on fetched rows."""
    return AnalysisTools()


def bind_sources(pipeline_or_source: SessionPipeline | Source, *sources: Source) -> Source:
    """Attach sources to a session and return a grouped source handle."""
    pipeline: SessionPipeline | None
    if isinstance(pipeline_or_source, Source):
        pipeline = None
        sources = (pipeline_or_source, *sources)
    else:
        pipeline = pipeline_or_source
    if not sources:
        raise ValueError("bind_sources() needs at least one source")
    for s in sources:
        if pipeline is not None:
            s.attach(pipeline)
    first = sources[0]
    grouped = Source(
        first.key,
        first.url,
        pipeline=pipeline,
        geo=first.geo,
        column_hints=list(first.column_hints),
        connector_type=first.connector_type,
        minor_source_keys=[s.key for s in sources],
        source_lookup={s.key: s for s in sources},
    )
    grouped._profile["cross_source_definitions"] = [
        {"source_key": s.key, "url": s.url} for s in sources
    ]
    grouped._sync_profile()
    return grouped


def combine_sources(
    pipeline: SessionPipeline,
    *sources: Source,
) -> CombinedSources:
    """Register every source on the session (order preserved)."""
    bind_sources(pipeline, *sources)
    return CombinedSources(pipeline, list(sources))


def combine_as_source(
    pipeline: SessionPipeline,
    key: str,
    *sources: Source,
    url: str = "session://combined",
) -> Source:
    """
    Register several sources and expose a lightweight synthetic source.

    Charts still point at their real source keys; the synthetic source stores
    cross-source definitions in its profile for clients/exporters that need to
    reason about the grouped feeds.
    """
    bound = bind_sources(pipeline, *sources)
    combined = Source(
        key,
        url,
        pipeline=pipeline,
        connector_type=_infer_connector_type(url),
        minor_source_keys=list(bound.minor_source_keys),
        source_lookup={s.key: s for s in sources},
    )
    combined._profile["cross_source_definitions"] = [
        {"source_key": s.key, "url": s.url} for s in sources
    ]
    combined._sync_profile()
    return combined


@dataclass
class Source:
    key: str
    url: str
    pipeline: SessionPipeline | None = None
    geo: GeoQueryResolver | None = None
    column_hints: list[str] = field(default_factory=list)
    connector_type: str = "csv"
    minor_source_keys: list[str] = field(default_factory=list)
    source_lookup: dict[str, Source] = field(default_factory=dict)
    analysis_steps: list[dict[str, Any]] = field(default_factory=list)
    _profile: dict = field(default_factory=dict, repr=False)
    _source_profiles: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.minor_source_keys:
            self.minor_source_keys = [self.key]
        if not self.source_lookup:
            self.source_lookup = {self.key: self}
        self._geo = self.geo or GeoQueryResolver()
        self._range = RangeQueryResolver()
        self._gis = GisQueryResolver()

    def require_pipeline(self) -> SessionPipeline:
        if self.pipeline is None:
            raise RuntimeError("Set pipeline= in source(), or call source.attach(pipeline) before charts / export.")
        return self.pipeline

    def hint_columns(self, names: list[str]) -> Source:
        """Seed fuzzy matching for :meth:`Charts.bar` / :meth:`Charts.foreach`."""
        self.column_hints = list(names)
        return self

    def _fuzzy(self) -> FuzzyColumnResolver | None:
        known = list(dict.fromkeys([*self.column_hints, *self._generic_column_hints()]))
        if not known:
            return None
        return FuzzyColumnResolver(known)

    def _generic_column_hints(self) -> list[str]:
        return [
            "year",
            "metric_value",
            "metric_name",
            "value",
            "count",
            "county",
            "city",
            "state",
            "observed_at",
            "latitude",
            "longitude",
            "lat",
            "lon",
            "lng",
            "x",
            "y",
            "OBJECTID",
            "YEAR_",
            "COUNTY",
        ]

    def _resolve_col(self, token: str | int) -> str:
        fz = self._fuzzy()
        if fz is None:
            return str(token)
        return fz.resolve(token)

    def near(
        self,
        place: str | tuple[float, float] | list[float] | dict[str, Any],
        distance: str | float | int,
        *,
        state: str | None = None,
        country: str | None = None,
        query_type: str = "auto",
        coordinate_columns: dict[str, list[str]] | None = None,
        source_keys: list[str] | None = None,
    ) -> Source:
        patch = self._geo.near(
            place,
            distance,
            state=state,
            country=country,
            query_type=query_type,  # type: ignore[arg-type]
            coordinate_columns=coordinate_columns,
        )
        self._apply_profile_patch(patch, source_keys=source_keys)
        return self

    def between(self, column: str, low: object, high: object, *, source_keys: list[str] | None = None) -> Source:
        patch = self._range.between(column, low, high)
        if "range_hints" in patch and "range_hints" in self._profile:
            patch = {**patch, "range_hints": [*self._profile["range_hints"], *patch["range_hints"]]}
        self._apply_profile_patch(patch, source_keys=source_keys)
        return self

    def observed_between(
        self,
        start: object,
        end: object,
        *,
        source_keys: list[str] | None = None,
    ) -> Source:
        return self.between("observed_at", start, end, source_keys=source_keys)

    def in_state(self, state_code: str, *, source_keys: list[str] | None = None) -> Source:
        self._apply_profile_patch({"state": state_code.strip()}, source_keys=source_keys)
        return self

    def metrics_named(self, *metric_names: str, source_keys: list[str] | None = None) -> Source:
        self._apply_profile_patch(
            {"metric_names": [str(m).strip() for m in metric_names if str(m).strip()]},
            source_keys=source_keys,
        )
        return self

    def hub_dataset(
        self,
        arcgis_hub_url: str,
        *,
        layer_name: str | None = None,
        source_keys: list[str] | None = None,
    ) -> Source:
        self._apply_profile_patch(self._gis.hub_context(arcgis_hub_url, layer_name=layer_name), source_keys=source_keys)
        return self

    def search(self, text: str, *, source_keys: list[str] | None = None) -> Source:
        self._apply_profile_patch({"search": text.strip()}, source_keys=source_keys)
        return self

    def in_county(self, county: str, *, source_keys: list[str] | None = None) -> Source:
        self._apply_profile_patch({"county": county.strip()}, source_keys=source_keys)
        return self

    def in_city(self, city: str, *, source_keys: list[str] | None = None) -> Source:
        self._apply_profile_patch({"city": city.strip()}, source_keys=source_keys)
        return self

    def year_range(
        self,
        year_min: int | None = None,
        year_max: int | None = None,
        *,
        source_keys: list[str] | None = None,
    ) -> Source:
        patch: dict[str, Any] = {}
        if year_min is not None:
            patch["year_min"] = year_min
        if year_max is not None:
            patch["year_max"] = year_max
        self._apply_profile_patch(patch, source_keys=source_keys)
        return self

    def _sync_profile(self) -> None:
        if self.pipeline and self.pipeline.session_id:
            from app.visualization_session import merge_source_query_profile

            merge_source_query_profile(self.pipeline.session_id, self.key, dict(self._profile))

    def _target_keys(self, source_keys: list[str] | None = None) -> list[str]:
        if source_keys:
            allowed = set(self.minor_source_keys)
            unknown = [k for k in source_keys if k not in allowed]
            if unknown:
                raise ValueError(f"Source keys not in grouped source: {unknown}")
            return list(source_keys)
        return [self.minor_source_keys[0]]

    def _apply_profile_patch(self, patch: dict[str, Any], *, source_keys: list[str] | None = None) -> None:
        targets = self._target_keys(source_keys)
        if targets == [self.key]:
            self._profile.update(patch)
            self._source_profiles[self.key] = {**self._source_profiles.get(self.key, {}), **patch}
            self._sync_profile()
            return
        for key in targets:
            self._source_profiles[key] = {**self._source_profiles.get(key, {}), **patch}
        if self.pipeline and self.pipeline.session_id:
            for key in targets:
                self.pipeline.apply_source_query_profile(key, patch)
        if self.key in targets:
            self._profile.update(patch)

    def fetch(
        self,
        db: Any = None,
        *,
        source_keys: list[str] | None = None,
        limit: int = 1000,
        print_rows: bool = False,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Query rows for this source. Grouped sources default to the first minor key."""
        keys = self._target_keys(source_keys)
        per_cap = max(1, limit // len(keys))
        rows: list[dict[str, Any]] = []
        for key in keys:
            if self.pipeline and self.pipeline.session_id:
                from app.visualization_session import get_session

                session = get_session(self.pipeline.session_id)
                session_profile = session.query_profile
                source_profile = {
                    **self._source_profiles.get(key, {}),
                    **session.source_query_profiles.get(key, {}),
                }
            else:
                session_profile = {}
                source_profile = self._source_profiles.get(key, self._profile if key == self.key else {})
            profile = effective_observation_filters(session_profile=session_profile, source_profile=source_profile, **filters)
            if db is not None:
                part = query_observations(db=db, source_key=key, limit=per_cap, **profile)
            else:
                part = self._fetch_direct_source(key, profile, limit=per_cap)
            for row in part:
                item = dict(row)
                item["session_source_key"] = key
                rows.append(item)
        out = rows[:limit]
        if print_rows:
            for row in out:
                print(row)
        return out

    def average_step(self, column: str, *, group_by: str | None = None, name: str | None = None) -> Source:
        self.analysis_steps.append({"type": "average", "column": column, "group_by": group_by, "name": name or f"avg_{column}"})
        return self

    def distribution_step(self, column: str, *, bins: int = 10, name: str | None = None) -> Source:
        self.analysis_steps.append({"type": "distribution", "column": column, "bins": bins, "name": name or f"dist_{column}"})
        return self

    def probability_step(self, column: str, value: Any, *, name: str | None = None) -> Source:
        self.analysis_steps.append({"type": "probability", "column": column, "value": value, "name": name or f"prob_{column}"})
        return self

    def bayes_step(
        self,
        hypothesis_column: str,
        hypothesis_value: Any,
        evidence_column: str,
        evidence_value: Any,
        *,
        name: str | None = None,
    ) -> Source:
        self.analysis_steps.append(
            {
                "type": "bayes",
                "hypothesis_column": hypothesis_column,
                "hypothesis_value": hypothesis_value,
                "evidence_column": evidence_column,
                "evidence_value": evidence_value,
                "name": name or "bayes",
            }
        )
        return self

    def region_distance_step(self, *, name: str = "region_distances") -> Source:
        self.analysis_steps.append({"type": "region_distances", "name": name})
        return self

    def intersection_step(self, *, radius_km: float = 10.0, name: str = "geometry_intersections") -> Source:
        self.analysis_steps.append({"type": "geometry_intersections", "radius_km": radius_km, "name": name})
        return self

    def regression_step(self, x: str, y: str, *, name: str | None = None) -> Source:
        self.analysis_steps.append({"type": "regression", "x": x, "y": y, "name": name or f"regression_{y}_on_{x}"})
        return self

    def run_analysis_steps(
        self,
        rows: list[dict[str, Any]] | None = None,
        *,
        tools: AnalysisTools | None = None,
    ) -> list[dict[str, Any]]:
        data = rows if rows is not None else self.fetch()
        engine = tools or AnalysisTools()
        return [engine.run_step(data, step) for step in self.analysis_steps]

    def transform_rows(
        self,
        rows: list[dict[str, Any]] | None = None,
        *,
        tools: AnalysisTools | None = None,
    ) -> list[dict[str, Any]]:
        data = rows if rows is not None else self.fetch()
        engine = tools or AnalysisTools()
        return engine.transform_rows(data, self.analysis_steps)

    def attach(self, pipeline: SessionPipeline) -> Source:
        """Register the source definition + dataset and push any accumulated query profile."""
        self.pipeline = pipeline
        pipeline.add_source(self.key, self.url)
        if self._profile:
            pipeline.apply_source_query_profile(self.key, self._profile)
        return self

    def register(self) -> Source:
        """Register this source for connector-backed direct fetches."""
        _register_direct_source(self)
        return self

    def _fetch_direct_source(self, source_key: str, profile: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
        target = self.source_lookup.get(source_key, self if source_key == self.key else None)
        if target is None:
            raise KeyError(f"Unknown source in grouped source: {source_key}")
        df = _fetch_source_dataframe(target)
        rows = _filter_rows(df.to_dict(orient="records"), profile)
        return rows[:limit]

    def as_chart_source(self) -> Source:
        """Document intent when a source is only used for charts/cross-source definitions."""
        return self


@dataclass
class Charts:
    definitions: list[dict[str, Any]] = field(default_factory=list)

    def _push_chart(self, source: Source, chart: dict[str, Any]) -> None:
        validate_chart_definition(chart)
        if source.pipeline and source.pipeline.session_id:
            source.pipeline.push_chart_dict(chart)
        else:
            self.definitions.append(chart)

    def _autosave(
        self,
        source: Source,
        chart_name: str,
        save_path: str | None = None,
        save_dir: str | None = None,
    ) -> None:
        if not save_path and not save_dir:
            return
        out = save_path
        if out is None:
            safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in chart_name).strip("_") or "chart"
            out = str(Path(save_dir or ".") / f"{safe}.svg")
        if source.pipeline and source.pipeline.session_id:
            source.pipeline.save_chart_picture(out, chart_name=chart_name)
            return
        for chart in reversed(self.definitions):
            if str(chart.get("name") or chart.get("name_prefix")) == chart_name:
                export_chart_spec_svg(chart, out)
                return
        raise ValueError(f"Chart not found by name: {chart_name}")

    def metric(
        self,
        source: Source,
        name: str,
        series: list[dict],
        *,
        layout: dict | None = None,
        notes: str | None = None,
        save_path: str | None = None,
        save_dir: str | None = None,
    ) -> Source:
        """Rich multi-source chart with optional ``style`` per trace and Plotly-style ``layout`` overrides."""
        self._push_chart(source, build_metric_chart(name, series, layout=layout, notes=notes))
        self._autosave(source, name, save_path=save_path, save_dir=save_dir)
        return source

    def bar(
        self,
        source: Source,
        value: str | int,
        category: str | int,
        *,
        name: str | None = None,
        save_path: str | None = None,
        save_dir: str | None = None,
    ) -> Source:
        """Bar-style counts or aggregates along ``category`` (e.g. ``year``)."""
        vc = source._resolve_col(value)
        cc = source._resolve_col(category)
        label = name or f"{vc}_by_{cc}"
        spec = BarChartSpec(
            name=label,
            source_key=source.minor_source_keys[0],
            category=cc,
            value=vc,
            aggregation="count",
        )
        self._push_chart(source, spec.model_dump())
        self._autosave(source, label, save_path=save_path, save_dir=save_dir)
        return source

    def scatter(
        self,
        source: Source,
        x: str | int,
        y: str | int,
        *,
        name: str | None = None,
        save_path: str | None = None,
        save_dir: str | None = None,
    ) -> Source:
        xs = source._resolve_col(x)
        ys = source._resolve_col(y)
        label = name or f"{ys}_vs_{xs}"
        spec = ScatterChartSpec(
            name=label,
            series=[ScatterSeries(source_key=source.minor_source_keys[0], x=xs, y=ys)],
        )
        self._push_chart(source, spec.model_dump())
        self._autosave(source, label, save_path=save_path, save_dir=save_dir)
        return source

    def foreach(
        self,
        source: Source,
        *columns: str | int,
        name_prefix: str = "pair",
        kind: str | None = None,
        kinds: tuple[str, ...] | None = None,
        save_dir: str | None = None,
    ) -> Source:
        """
        Split column names: first half → X family, second half → Y family; emit a :class:`ForeachChartSpec`.

        Pass ``kinds=("scatter","bar")`` or ``kind="scatter,bar"`` to fan out chart kinds.
        """
        if len(columns) < 2:
            raise ValueError("foreach() needs at least two column names")
        mid = len(columns) // 2
        xs = [source._resolve_col(c) for c in columns[:mid]]
        ys = [source._resolve_col(c) for c in columns[mid:]]
        if kinds is not None:
            klist = list(kinds)
        elif kind is not None:
            klist = [s.strip() for s in kind.split(",") if s.strip()]
        else:
            klist = ["scatter"]
        spec = ForeachChartSpec(
            name_prefix=name_prefix,
            source_key=source.minor_source_keys[0],
            x_columns=xs,
            y_columns=ys,
            chart_kinds=klist,  # type: ignore[arg-type]
        )
        self._push_chart(source, spec.model_dump())
        if save_dir:
            raise RuntimeError("Direct foreach image export requires a session-backed pipeline.")
        return source

    def foreach_expand(
        self,
        source: Source,
        *columns: str | int,
        name_prefix: str = "grid",
        kinds: tuple[str, ...] = ("scatter", "bar"),
        save_dir: str | None = None,
    ) -> Source:
        """Fully expand scatter **and** bar charts for every column pair (see :meth:`SessionPipeline.foreach_expand_pairs`)."""
        if len(columns) < 2:
            raise ValueError("foreach_expand needs at least two column names")
        mid = len(columns) // 2
        xs = [source._resolve_col(c) for c in columns[:mid]]
        ys = [source._resolve_col(c) for c in columns[mid:]]
        expanded = expand_pair_grid(
            source.minor_source_keys[0],
            xs,
            ys,
            kinds=kinds,
            name_prefix=name_prefix,
        )
        for spec in expanded:
            self._push_chart(source, spec)
        if save_dir:
            raise RuntimeError("Direct foreach image export requires a session-backed pipeline.")
        return source

    def foreach_ranges(
        self,
        source: Source,
        x: str | int,
        y: str | int,
        year_ranges: list[tuple[int, int]],
        *,
        base_name: str = "slice",
        save_dir: str | None = None,
    ) -> Source:
        """Emit metric charts annotated with ``filter_slice`` year windows."""
        expanded = expand_metric_ranges(
            source.minor_source_keys[0],
            source._resolve_col(x),
            source._resolve_col(y),
            year_ranges,
            base_name=base_name,
        )
        for spec in expanded:
            self._push_chart(source, spec)
        if save_dir:
            raise RuntimeError("Direct foreach image export requires a session-backed pipeline.")
        return source

    def overlay(
        self,
        source: Source,
        name: str,
        overlays: list[tuple[str, tuple[str, ...]]],
        *,
        save_path: str | None = None,
    ) -> Source:
        spec = MultiOverlayChartSpec(
            name=name,
            overlays=[OverlaySeries(source_key=key, columns=columns) for key, columns in overlays],
        )
        self._push_chart(source, spec.model_dump())
        self._autosave(source, name, save_path=save_path)
        return source

    def sankey(self, source: Source, name: str, *, source_keys: list[str] | None = None, save_path: str | None = None) -> Source:
        spec = SankeyChartSpec(name=name, source_keys=source_keys or source.minor_source_keys)
        self._push_chart(source, spec.model_dump())
        self._autosave(source, name, save_path=save_path)
        return source

    def heatmap(self, source: Source, name: str, x: str, y: str, z: str, *, save_path: str | None = None) -> Source:
        spec = HeatmapChartSpec(name=name, source_key=source.minor_source_keys[0], x=x, y=y, z=z)
        self._push_chart(source, spec.model_dump())
        self._autosave(source, name, save_path=save_path)
        return source

    def correlation_matrix(
        self,
        source: Source,
        name: str,
        *,
        variables: list[str] | None = None,
        source_keys: list[str] | None = None,
        save_path: str | None = None,
    ) -> Source:
        spec = CorrelationMatrixSpec(name=name, source_keys=source_keys or source.minor_source_keys, variables=variables or [])
        self._push_chart(source, spec.model_dump())
        self._autosave(source, name, save_path=save_path)
        return source

    def cross_pair(
        self,
        source: Source,
        name: str,
        left: tuple[str, str, str],
        right: tuple[str, str, str],
        *,
        save_path: str | None = None,
    ) -> Source:
        spec = CrossPairChartSpec(
            name=name,
            left_source_key=left[0],
            left_x=left[1],
            left_y=left[2],
            right_source_key=right[0],
            right_x=right[1],
            right_y=right[2],
        )
        self._push_chart(source, spec.model_dump())
        self._autosave(source, name, save_path=save_path)
        return source

    def render_python(
        self,
        rows_by_source: dict[str, list[dict[str, Any]]],
        output_dir: str | Path,
        *,
        fmt: str = "png",
    ) -> list[str]:
        return render_charts_python(self.definitions, rows_by_source, output_dir, fmt=fmt)


def _infer_connector_type(url: str) -> str:
    lower = url.lower()
    if "arcgis/rest" in lower or "mapserver" in lower or "featureserver" in lower:
        return "arcgis_rest"
    if lower.endswith((".xlsx", ".xls")):
        return "excel"
    if lower.endswith((".geojson", ".json")) and "arcgis/rest" not in lower:
        return "geojson"
    return "csv"


def _register_direct_source(source: Source) -> SourceDefinition:
    definition = SourceDefinition(
        source_key=source.key,
        display_name=source.key,
        category="direct",
        connector_type=source.connector_type,
        source_url=source.url,
    )
    return add_or_update_source(definition)


def _fetch_source_dataframe(source: Source):
    from app.connectors.factory import create_connector

    try:
        definition = get_source(source.key)
    except KeyError:
        definition = _register_direct_source(source)
    connector = create_connector(definition)
    return connector.fetch()


def _row_float(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _matches_text(value: Any, expected: str) -> bool:
    return str(value or "").strip().lower() == expected.strip().lower()


def _contains_text(row: dict[str, Any], needle: str) -> bool:
    q = needle.strip().lower()
    if not q:
        return True
    fields = ("county", "city", "metric_name", "observation_type", "state")
    return any(q in str(row.get(field, "")).lower() for field in fields)


def _within_radius(row: dict[str, Any], latitude: float, longitude: float, radius_km: float) -> bool:
    from math import asin, cos, radians, sin, sqrt

    lat = _row_float(row, "latitude", "lat", "lat_dd", "y")
    lon = _row_float(row, "longitude", "lon", "lng", "long_dd", "x")
    if lat is None or lon is None:
        return False
    dlat = radians(lat - latitude)
    dlon = radians(lon - longitude)
    a = sin(dlat / 2) ** 2 + cos(radians(latitude)) * cos(radians(lat)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(a)) <= radius_km


def _filter_rows(rows: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if profile.get("state") and not _matches_text(row.get("state"), profile["state"]):
            continue
        if profile.get("county") and not _matches_text(row.get("county"), profile["county"]):
            continue
        if profile.get("city") and not _matches_text(row.get("city"), profile["city"]):
            continue
        year = _row_float(row, "year", "YEAR_", "fireyear", "fire_year", "incident_year")
        if profile.get("year_min") is not None and (year is None or year < float(profile["year_min"])):
            continue
        if profile.get("year_max") is not None and (year is None or year > float(profile["year_max"])):
            continue
        metric_value = _row_float(row, "metric_value", "value", "count", "esttotalacres", "protected_acres", "ANNUAL_COS", "REPAIR_COS")
        if profile.get("metric_value_min") is not None and (
            metric_value is None or metric_value < float(profile["metric_value_min"])
        ):
            continue
        if profile.get("metric_value_max") is not None and (
            metric_value is None or metric_value > float(profile["metric_value_max"])
        ):
            continue
        metric_names = profile.get("metric_names")
        if metric_names and row.get("metric_name") not in metric_names:
            continue
        if profile.get("search") and not _contains_text(row, str(profile["search"])):
            continue
        if (
            profile.get("latitude") is not None
            and profile.get("longitude") is not None
            and profile.get("radius_km") is not None
            and not _within_radius(
                row,
                float(profile["latitude"]),
                float(profile["longitude"]),
                float(profile["radius_km"]),
            )
        ):
            continue
        out.append(row)
    return out


@dataclass
class AnalysisTools:
    """Direct equivalents of the API analysis tools, operating on in-process rows."""

    backend: str = "python"

    def available_backends(self) -> dict[str, Any]:
        from shutil import which

        from app.analysis import R_RUNNER

        return {
            "python": {"available": True, "modes": ["average", "distribution", "probability", "bayes", "geometry", "correlation", "regression"]},
            "r": {"available": bool(which("Rscript") and R_RUNNER.exists()), "runner": str(R_RUNNER)},
            "matlab": {"available": bool(which("matlab")), "command": "matlab"},
        }

    def add_average_variable(
        self,
        rows: list[dict[str, Any]],
        column: str,
        *,
        group_by: str | None = None,
        output_column: str | None = None,
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        if df.empty or column not in df.columns:
            return rows
        out_col = output_column or f"{column}_average"
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if group_by and group_by in df.columns:
            df[out_col] = df.groupby(group_by)[column].transform("mean")
        else:
            df[out_col] = df[column].mean()
        return df.to_dict(orient="records")

    def add_distribution_variable(
        self,
        rows: list[dict[str, Any]],
        column: str,
        *,
        bins: int = 10,
        output_column: str | None = None,
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        if df.empty or column not in df.columns:
            return rows
        out_col = output_column or f"{column}_distribution_bin"
        numeric = pd.to_numeric(df[column], errors="coerce")
        df[out_col] = pd.cut(numeric, bins=bins).astype(str)
        return df.to_dict(orient="records")

    def add_probability_variable(
        self,
        rows: list[dict[str, Any]],
        column: str,
        value: Any,
        *,
        output_column: str | None = None,
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        if df.empty or column not in df.columns:
            return rows
        out_col = output_column or f"probability_{column}_{value}"
        df[out_col] = (df[column].astype(str) == str(value)).mean()
        return df.to_dict(orient="records")

    def add_bayes_variable(
        self,
        rows: list[dict[str, Any]],
        hypothesis_column: str,
        hypothesis_value: Any,
        evidence_column: str,
        evidence_value: Any,
        *,
        output_column: str | None = None,
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        if df.empty or hypothesis_column not in df.columns or evidence_column not in df.columns:
            return rows
        evidence = df[evidence_column].astype(str) == str(evidence_value)
        posterior = ((df[hypothesis_column].astype(str) == str(hypothesis_value)) & evidence).sum() / evidence.sum() if evidence.sum() else 0.0
        df[output_column or "bayes_posterior"] = posterior
        return df.to_dict(orient="records")

    def add_regression_variable(
        self,
        rows: list[dict[str, Any]],
        *,
        x: str,
        y: str,
        output_column: str | None = None,
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        result = self.regression(rows, x=x, y=y)
        if result.get("status") != "ok" or x not in df.columns:
            return rows
        df[output_column or f"{y}_regression_prediction"] = result["slope"] * pd.to_numeric(df[x], errors="coerce") + result["intercept"]
        return df.to_dict(orient="records")

    def aggregate_source(
        self,
        rows: list[dict[str, Any]],
        *,
        group_by: list[str],
        value: str,
        aggregations: tuple[str, ...] = ("count", "mean", "sum"),
        source_key: str = "derived_aggregate",
    ) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if df.empty or value not in df.columns:
            return []
        for col in group_by:
            if col not in df.columns:
                return []
        df[value] = pd.to_numeric(df[value], errors="coerce")
        agg_map: dict[str, str] = {}
        if "count" in aggregations:
            agg_map[f"{value}_count"] = "count"
        if "mean" in aggregations:
            agg_map[f"{value}_mean"] = "mean"
        if "sum" in aggregations:
            agg_map[f"{value}_sum"] = "sum"
        grouped = df.groupby(group_by)[value].agg(**agg_map).reset_index()
        out = grouped.to_dict(orient="records")
        for row in out:
            row["session_source_key"] = source_key
        return out

    def run_step(self, rows: list[dict[str, Any]], step: dict[str, Any]) -> dict[str, Any]:
        stype = step.get("type")
        if stype == "average":
            result = self.average(rows, str(step["column"]), group_by=step.get("group_by"))
        elif stype == "distribution":
            result = self.distribution(rows, str(step["column"]), bins=int(step.get("bins", 10)))
        elif stype == "probability":
            result = self.probability(rows, str(step["column"]), step.get("value"))
        elif stype == "bayes":
            result = self.bayes(
                rows,
                str(step["hypothesis_column"]),
                step.get("hypothesis_value"),
                str(step["evidence_column"]),
                step.get("evidence_value"),
            )
        elif stype == "region_distances":
            result = self.region_distances(rows)
        elif stype == "geometry_intersections":
            result = self.geometry_intersections(rows, radius_km=float(step.get("radius_km", 10.0)))
        elif stype == "regression":
            result = self.regression(rows, x=str(step["x"]), y=str(step["y"]))
        else:
            result = {"status": "failed", "error": f"Unsupported analysis step: {stype}"}
        return {"name": step.get("name", stype), "type": stype, "result": result}

    def average(self, rows: list[dict[str, Any]], column: str, *, group_by: str | None = None) -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if column not in df.columns:
            return {"status": "failed", "error": f"Missing column: {column}"}
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if group_by and group_by in df.columns:
            values = df.groupby(group_by)[column].mean().dropna().to_dict()
            return {"status": "ok", "column": column, "group_by": group_by, "averages": values}
        return {"status": "ok", "column": column, "average": float(df[column].mean())}

    def distribution(self, rows: list[dict[str, Any]], column: str, *, bins: int = 10) -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if column not in df.columns:
            return {"status": "failed", "error": f"Missing column: {column}"}
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            return {"status": "ok", "column": column, "bins": []}
        counts, edges = pd.cut(series, bins=bins, retbins=True)
        grouped = counts.value_counts(sort=False)
        return {
            "status": "ok",
            "column": column,
            "bins": [
                {"low": float(interval.left), "high": float(interval.right), "count": int(count)}
                for interval, count in grouped.items()
            ],
        }

    def probability(self, rows: list[dict[str, Any]], column: str, value: Any) -> dict[str, Any]:
        total = len(rows)
        if total == 0:
            return {"status": "ok", "column": column, "value": value, "probability": 0.0, "count": 0, "total": 0}
        count = sum(1 for row in rows if str(row.get(column)) == str(value))
        return {"status": "ok", "column": column, "value": value, "probability": count / total, "count": count, "total": total}

    def bayes(
        self,
        rows: list[dict[str, Any]],
        hypothesis_column: str,
        hypothesis_value: Any,
        evidence_column: str,
        evidence_value: Any,
    ) -> dict[str, Any]:
        total = len(rows)
        if total == 0:
            return {"status": "ok", "posterior": 0.0, "count": 0, "evidence_count": 0}
        evidence = [row for row in rows if str(row.get(evidence_column)) == str(evidence_value)]
        both = [row for row in evidence if str(row.get(hypothesis_column)) == str(hypothesis_value)]
        posterior = len(both) / len(evidence) if evidence else 0.0
        return {
            "status": "ok",
            "posterior": posterior,
            "hypothesis": {hypothesis_column: hypothesis_value},
            "evidence": {evidence_column: evidence_value},
            "count": len(both),
            "evidence_count": len(evidence),
        }

    def region_distances(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        from math import asin, cos, radians, sin, sqrt

        points: list[tuple[int, float, float]] = []
        for idx, row in enumerate(rows):
            lat = _row_float(row, "latitude", "lat", "lat_dd", "y")
            lon = _row_float(row, "longitude", "lon", "lng", "long_dd", "x")
            if lat is not None and lon is not None:
                points.append((idx, lat, lon))
        distances: list[dict[str, Any]] = []
        for i, lat_a, lon_a in points:
            for j, lat_b, lon_b in points:
                if j <= i:
                    continue
                dlat = radians(lat_b - lat_a)
                dlon = radians(lon_b - lon_a)
                a = sin(dlat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(dlon / 2) ** 2
                km = 6371.0088 * 2 * asin(sqrt(a))
                distances.append({"left_index": i, "right_index": j, "distance_km": km})
        return {"status": "ok", "pair_count": len(distances), "distances": distances}

    def geometry_intersections(self, rows: list[dict[str, Any]], *, radius_km: float = 10.0) -> dict[str, Any]:
        try:
            from shapely.geometry import Point
        except Exception as exc:  # pragma: no cover
            return {"status": "failed", "error": f"shapely unavailable: {exc}"}

        geometries: list[tuple[int, Any]] = []
        radius_degrees = radius_km / 111.0
        for idx, row in enumerate(rows):
            lat = _row_float(row, "latitude", "lat", "lat_dd", "y")
            lon = _row_float(row, "longitude", "lon", "lng", "long_dd", "x")
            if lat is not None and lon is not None:
                geometries.append((idx, Point(lon, lat).buffer(radius_degrees)))
        intersections: list[dict[str, Any]] = []
        for left_idx, left_geom in geometries:
            for right_idx, right_geom in geometries:
                if right_idx <= left_idx:
                    continue
                if left_geom.intersects(right_geom):
                    intersections.append(
                        {
                            "left_index": left_idx,
                            "right_index": right_idx,
                            "overlap_area_degrees": float(left_geom.intersection(right_geom).area),
                        }
                    )
        return {"status": "ok", "radius_km": radius_km, "intersections": intersections}

    def distinct_regions(self, rows: list[dict[str, Any]], *, region_column: str = "county") -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if region_column not in df.columns:
            return {"status": "failed", "error": f"Missing region column: {region_column}"}
        if "latitude" in df.columns and "longitude" in df.columns:
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
            grouped = df.groupby(region_column).agg(
                count=(region_column, "count"),
                latitude=("latitude", "mean"),
                longitude=("longitude", "mean"),
            )
        else:
            grouped = df.groupby(region_column).agg(count=(region_column, "count"))
        return {"status": "ok", "region_column": region_column, "regions": grouped.reset_index().to_dict(orient="records")}

    def plot_regions(
        self,
        rows: list[dict[str, Any]],
        output_path: str | Path,
        *,
        region_column: str = "county",
        intersection_radius_km: float = 10.0,
    ) -> str:
        import pandas as pd
        from app.workflow.chart_rendering import _ensure_matplotlib

        plt = _ensure_matplotlib()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111)
        if {"latitude", "longitude"}.issubset(df.columns):
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
            for region, subset in df.dropna(subset=["latitude", "longitude"]).groupby(region_column):
                ax.scatter(subset["longitude"], subset["latitude"], label=str(region), s=50)
                cx = subset["longitude"].mean()
                cy = subset["latitude"].mean()
                ax.text(cx, cy, str(region), fontsize=9)
            intersections = self.geometry_intersections(rows, radius_km=intersection_radius_km).get("intersections", [])
            for item in intersections:
                left = df.iloc[int(item["left_index"])]
                right = df.iloc[int(item["right_index"])]
                ax.plot([left["longitude"], right["longitude"]], [left["latitude"], right["latitude"]], color="#d62728", alpha=0.35)
        ax.set_title("Distinct regions and approximate intersections")
        ax.set_xlabel("longitude")
        ax.set_ylabel("latitude")
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(out, dpi=150)
        plt.close(fig)
        return str(out)

    def transform_rows(self, rows: list[dict[str, Any]], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        import pandas as pd

        df = pd.DataFrame(rows).copy()
        if df.empty:
            return []
        for step in steps:
            stype = step.get("type")
            if stype == "average":
                column = str(step["column"])
                group_by = step.get("group_by")
                out_col = str(step.get("name") or f"avg_{column}")
                if column in df.columns:
                    df[column] = pd.to_numeric(df[column], errors="coerce")
                    if group_by and group_by in df.columns:
                        df[out_col] = df.groupby(group_by)[column].transform("mean")
                    else:
                        df[out_col] = df[column].mean()
            elif stype == "distribution":
                column = str(step["column"])
                out_col = str(step.get("name") or f"dist_{column}")
                if column in df.columns:
                    numeric = pd.to_numeric(df[column], errors="coerce")
                    df[out_col] = pd.cut(numeric, bins=int(step.get("bins", 10))).astype(str)
            elif stype == "probability":
                column = str(step["column"])
                value = step.get("value")
                out_col = str(step.get("name") or f"prob_{column}")
                if column in df.columns:
                    prob = (df[column].astype(str) == str(value)).mean()
                    df[out_col] = prob
            elif stype == "bayes":
                h_col = str(step["hypothesis_column"])
                h_val = step.get("hypothesis_value")
                e_col = str(step["evidence_column"])
                e_val = step.get("evidence_value")
                out_col = str(step.get("name") or "bayes")
                if h_col in df.columns and e_col in df.columns:
                    evidence = df[e_col].astype(str) == str(e_val)
                    posterior = ((df[h_col].astype(str) == str(h_val)) & evidence).sum() / evidence.sum() if evidence.sum() else 0.0
                    df[out_col] = posterior
            elif stype == "regression":
                x = str(step["x"])
                y = str(step["y"])
                out_col = str(step.get("name") or f"regression_{y}_on_{x}")
                result = self.regression(df.to_dict(orient="records"), x=x, y=y)
                if result.get("status") == "ok" and x in df.columns:
                    df[out_col] = result["slope"] * pd.to_numeric(df[x], errors="coerce") + result["intercept"]
        return df.to_dict(orient="records")

    def correlation(self, rows: list[dict[str, Any]], variables: list[str] | None = None) -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if variables:
            cols = [c for c in variables if c in df.columns]
        else:
            cols = list(df.select_dtypes(include="number").columns)
        if not cols:
            return {"status": "ok", "variables": [], "correlation": {}}
        numeric = df[cols].apply(pd.to_numeric, errors="coerce")
        return {
            "status": "ok",
            "variables": cols,
            "correlation": numeric.corr().fillna(0).to_dict(),
        }

    def regression(self, rows: list[dict[str, Any]], *, x: str = "year", y: str = "metric_value") -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if x not in df.columns or y not in df.columns:
            return {"status": "failed", "error": f"Missing regression columns: {x}, {y}"}
        xs = pd.to_numeric(df[x], errors="coerce")
        ys = pd.to_numeric(df[y], errors="coerce")
        keep = xs.notna() & ys.notna()
        xs = xs[keep]
        ys = ys[keep]
        if len(xs) < 2:
            return {"status": "failed", "error": "Regression requires at least two numeric rows."}
        slope = float(((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum())
        intercept = float(ys.mean() - slope * xs.mean())
        return {"status": "ok", "x": x, "y": y, "slope": slope, "intercept": intercept, "n": int(len(xs))}

    def county_compare(self, rows: list[dict[str, Any]], *, value: str = "metric_value") -> dict[str, Any]:
        import pandas as pd

        df = pd.DataFrame(rows)
        if "county" not in df.columns or value not in df.columns:
            return {"status": "failed", "error": f"Missing county or {value} columns."}
        df[value] = pd.to_numeric(df[value], errors="coerce")
        grouped = (
            df.dropna(subset=["county", value])
            .groupby("county")[value]
            .agg(["count", "mean", "sum"])
            .sort_values("sum", ascending=False)
        )
        return {"status": "ok", "counties": grouped.reset_index().to_dict(orient="records")}


@dataclass
class CombinedSources:
    pipeline: SessionPipeline
    sources: list[Source]
    cross: CrossSourceSolver = field(init=False)
    series: SeriesSolver = field(init=False)

    def __post_init__(self) -> None:
        self.cross = CrossSourceSolver(self.pipeline)
        self.series = SeriesSolver(self.pipeline)

    def pair_variables(
        self,
        name: str,
        left: tuple[str, str, str],
        right: tuple[str, str, str],
    ) -> SessionPipeline:
        """``(source_key, x, y)`` per side — thin wrapper on :class:`CrossSourceSolver`."""
        return self.cross.scatter_pair(name, left, right)

    def metric_chart(
        self,
        name: str,
        series: list[dict],
        *,
        layout: dict | None = None,
        notes: str | None = None,
    ) -> SessionPipeline:
        """Combine arbitrary traces (different sources/columns) with styling before export."""
        return self.pipeline.push_chart_dict(build_metric_chart(name, series, layout=layout, notes=notes))

    def save_chart_picture(
        self,
        output_path: str,
        *,
        chart_name: str | None = None,
        chart_index: int = -1,
    ) -> str:
        """Proxy to :meth:`SessionPipeline.save_chart_picture`."""
        return self.pipeline.save_chart_picture(output_path, chart_name=chart_name, chart_index=chart_index)

    def save_analysis_picture(self, title: str, lines: list[str], output_path: str) -> str:
        """Proxy to :meth:`SessionPipeline.save_analysis_picture`."""
        return self.pipeline.save_analysis_picture(title, lines, output_path)

    def save_defined_chart_images(self, output_dir: str, *, fmt: str = "png") -> list[str]:
        """Render and save images from chart definitions created via `.charts.*(...)`."""
        return self.pipeline.save_defined_chart_images(output_dir, fmt=fmt)

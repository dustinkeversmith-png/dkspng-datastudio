"""High-level session workflow facades."""

from app.workflow.data_reshape import DataReshaper
from app.workflow.chart_foreach_expand import expand_pair_grid, materialize_foreach_spec
from app.workflow.picture_export import export_analysis_svg, export_chart_spec_svg
from app.workflow.chart_query import build_metric_chart
from app.workflow.definition_chart_export import render_defined_charts_to_images
from app.workflow.chart_rendering import render_chart_python, render_charts_python
from app.workflow.query import (
    FuzzyColumnResolver,
    GeoQueryResolver,
    GisQueryResolver,
    RangeQueryResolver,
    SelectionCommandParser,
)
from app.workflow.session_pipeline import ColumnResolver, SessionPipeline
from app.workflow.solvers import CrossSourceSolver, SeriesSolver
from app.workflow.source_binding import (
    CombinedSources,
    Charts,
    Source,
    analysis_tools,
    bind_sources,
    charts,
    combine_as_source,
    combine_sources,
    source,
)

__all__ = [
    "SessionPipeline",
    "ColumnResolver",
    "DataReshaper",
    "Source",
    "Charts",
    "CombinedSources",
    "analysis_tools",
    "bind_sources",
    "charts",
    "combine_as_source",
    "combine_sources",
    "source",
    "GeoQueryResolver",
    "GisQueryResolver",
    "RangeQueryResolver",
    "FuzzyColumnResolver",
    "SelectionCommandParser",
    "CrossSourceSolver",
    "SeriesSolver",
    "build_metric_chart",
    "expand_pair_grid",
    "materialize_foreach_spec",
    "export_chart_spec_svg",
    "export_analysis_svg",
    "render_defined_charts_to_images",
    "render_chart_python",
    "render_charts_python",
]

"""
Final Integration Test — Regional Data Studio

Exercises the complete new Source API:

  Mapping         set_map / map / append
  Indexing        DSL string expressions ("1..3", "col1, col2")
  Column IDs      colids (int-keyed) / names (multi-source)
  Semantic roles  s.name()
  Discovery       find_matching_types / find_matching_units
  Mutation        s.add() / s.remove()
  Conditionals    s.if_().add()
  Analysis        s.log_regression() → RegressionResult
                  s.knn()            → KNNResult
  Visualisation   s.bar() / s.scatter() → Chart
                  chart.linefn() / chart.points() → Chart
                  chart.save()       → VisualObject (with .legend)
"""

import pytest

from app.workflow.source_binding import source, Source
from app.schemas import SourceDefinition
from app.operations.data_ops import check_base_types
from app.visualizations.chart import VisualObject, LegendObject
from app.visualizations.hint import hint, VisualHint
from app.analysis.results import RegressionResult, KNNResult
from app.mappings.column import Column


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fire_def():
    return SourceDefinition(
        source_key="fire",
        display_name="Fire Data",
        category="test",
        connector_type="csv",
        source_url="tests/fixtures/sources/fire_occurrences.csv",
    )


@pytest.fixture
def pop_def():
    return SourceDefinition(
        source_key="pop",
        display_name="Population Data",
        category="test",
        connector_type="csv",
        source_url="tests/fixtures/sources/population.csv",
    )


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

def test_final_integration(fire_def, pop_def):

    # 1. Create a source; add a second sub-source ─────────────────────────
    s = source(fire_def).add_source(pop_def)

    # Register a named mapping between columns (set_map = register only)
    s.set_map(
        name="metric_conversion",
        from_loc=("fire", 3),              # column index 3 of fire
        to_loc=("pop", "converted_metric"),
        func=lambda val: val * 2 if isinstance(val, (int, float)) else val,
    )

    # Execute the mapping → returns a Column object (like a standalone column)
    result_column = s.map("metric_conversion", "all")
    assert isinstance(result_column, Column)

    # Append that column into a sub-source
    s.append(result_column, {"fire", "metric_conversion"})

    assert "fire" in s.dataframes
    assert "pop" in s.dataframes

    # 2. Subset columns from both sub-sources ─────────────────────────────
    s_sub = s.subset({
        "fire": ["incident_id", "acres_burned", "latitude", "longitude"],
        "pop":  ["county", "population"],
    })
    assert isinstance(s_sub, Source)
    assert "incident_id" in s_sub.dataframes["fire"].columns

    # 3. Generate metadata ────────────────────────────────────────────────
    s_sub.generate_metadata()
    assert "fire" in s_sub.metadata

    # Index with DSL strings  ("1..3" = rows 1-2, "col1, col2" = cols by name)
    new_source = s_sub.index(
        fire=("1..3", "incident_id, acres_burned"),
        pop=(slice(0, 4), slice(0, 2)),
    )
    assert isinstance(new_source, Source)
    assert len(new_source.dataframes["fire"]) == 2   # rows 1, 2

    # Column IDs — integer-keyed dict
    cols = s_sub.colids("fire")
    assert 0 in cols                                 # {0: "incident_id", ...}
    assert isinstance(cols[0], str)

    # Names for multiple sub-sources
    names = s_sub.names({"fire", "pop"})
    assert "fire" in names
    assert "pop" in names
    assert 0 in names["fire"]

    # Semantic naming — rename columns via .name()
    s_sub.name("fire", {"acres_burned": "burn_area", "latitude": "lat"})
    assert "burn_area" in s_sub.dataframes["fire"].columns

    # Discovery — find columns sharing types across sources
    matches = s_sub.find_matching_types({"fire", "pop"}, {"numeric", "spatial"})
    assert isinstance(matches, dict)

    # Find matching unit columns (returns cross-source indexing tuples)
    units = s_sub.find_matching_units({"fire", "pop"})
    assert isinstance(units, dict)
    assert "matching_unit_columns" in units
    assert "cross_index" in units

    # Make a direct copy
    s_sub_copy = s_sub.copy()
    assert isinstance(s_sub_copy, Source)

    # Check base types
    types = check_base_types(s_sub, "fire")
    assert types.get("burn_area") == "numeric"   # was acres_burned before rename

    # 4. Mutation via .add() and .remove() ────────────────────────────────

    # Add a computed column from a cross-source expression
    s_sub.add(
        ("fire", "risk_factor"),
        "mean(fire[burn_area]) * 1.5",
    )
    assert "risk_factor" in s_sub.dataframes["fire"].columns

    # Remove a column by AxisExpr reference
    s_sub.remove(s_sub["fire"]["risk_factor"])
    assert "risk_factor" not in s_sub.dataframes["fire"].columns

    # Conditional add — only set high_risk where burn_area > 10
    s_sub.if_(s_sub["fire"]["burn_area"] > 10).add(
        ("fire", "high_risk"),
        "1",
    )
    assert "high_risk" in s_sub.dataframes["fire"].columns

    # 5. Analysis ─────────────────────────────────────────────────────────
    reg = s_sub.log_regression(
        source_key="fire",
        features=["burn_area"],
        target="lat",
    )
    assert isinstance(reg, RegressionResult)
    assert isinstance(reg.weights, list)
    assert isinstance(reg.bias, float)

    knn_result = s_sub.knn(
        source_key="fire",
        features=["burn_area"],
        target="lat",
        n_neighbors=3,
    )
    assert isinstance(knn_result, KNNResult)

    # 6. Visualisation ────────────────────────────────────────────────────

    # AxisExpr-based bar chart (implied axis from SourceProxy)
    chart = s_sub.bar(s_sub["fire"]["burn_area"], s_sub["fire"]["lat"])


    # automatically updating the legend
    chart.legend.color("fire[burn_area]", "black")
    chart.legend.size("fire[burn_area]", "4px")
    chart.legend.opacity("fire[burn_area]", "0.5")

    # Overlay regression line and KNN points
    chart.linefn(reg.weights, reg.bias)
    chart.points(knn_result.points)

    # Save → VisualObject with .legend
    chart_object = chart.save("test_chart.png")
    assert isinstance(chart_object, VisualObject)
    assert isinstance(chart_object.legend, LegendObject)

    # Scatter chart  (filtered axis with .where())
    scatter_chart = s_sub.scatter(
        s_sub["fire"]["burn_area"].mean().where(s_sub["fire"]["lat"] > 40),
        s_sub["fire"]["lat"],
    )
    scatter_obj = scatter_chart.save("test_scatter.png")
    assert isinstance(scatter_obj, VisualObject)

    # Adding visual hints for categorical variables
    # hint(sources, fields) → VisualHint
    vishint = hint({"fire", "pop"}, {"fire_type"})
    assert isinstance(vishint, VisualHint)

    # Tag the geometry type for spatial rendering
    vishint.geo("polygon")
    assert vishint._geo == "polygon"

    # Spatial bounding box — accepts AxisExpr .min()/.max() calls
    vishint.bounds(
        s_sub["fire"]["lat"].min(),
        s_sub["fire"]["lat"].max(),
        s_sub["fire"]["longitude"].min(),
        s_sub["fire"]["longitude"].max(),
    )
    assert vishint._bounds is not None

    # Micro-DSL programs — projection and categorical encoding
    vishint.projection(
        "i",
        "for(e=input.dim(),2), i[0] /= i[e], i[1] / i[e]",
    )
    vishint.encode(
        "i",
        "i.catcode / input.dim()",
    )
    assert len(vishint._programs) == 2
    assert vishint._programs[0]["kind"] == "projection"
    assert vishint._programs[1]["kind"] == "encode"

    # Attach the hint to the chart before save
    chart.apply_hint(vishint)
    assert len(chart._hints) == 1

    # GIS Tool (kept for spatial verification)
    from app.gis_tools.topological import intersection_buffer
    gis_res = intersection_buffer(s_sub, "fire", "pop")
    assert "error" in gis_res or "status" in gis_res

    # Views (metadata string check)
    from app.views.source_views import metadata_view
    meta_str = metadata_view(s_sub, "fire")
    assert "burn_area" in meta_str

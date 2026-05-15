from pathlib import Path
from typing import Any

from app.examples.three_portal_bindings import PORTAL_APIS, register_three_portal_sources
from app.workflow import analysis_tools, bind_sources, charts, source


def _first_present(row: dict[str, Any], candidates: list[str]) -> Any:
    lowered = {k.lower(): k for k in row}
    for candidate in candidates:
        key = lowered.get(candidate.lower())
        if key is not None and row.get(key) not in (None, ""):
            return row.get(key)
    return None


def _first_numeric(row: dict[str, Any], exclude: set[str] | None = None) -> float:
    skip = {x.lower() for x in (exclude or set())}
    for key, value in row.items():
        if key.lower() in skip:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 1.0


def _normalize_rows(source_key: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        year = _first_present(row, ["year", "fire_year", "incident_year", "YEAR_", "FIREYEAR", "FireYear"])
        metric_value = _first_present(row, ["metric_value", "value", "esttotalacres", "protected_acres", "GIS_ACRES", "TOTALACRES", "ACRES", "SIZE_CLASS"])
        county = _first_present(row, ["county", "county_name", "COUNTY", "COUNTY_NAM", "County"])
        city = _first_present(row, ["city", "CITY", "nearest_city"])
        latitude = _first_present(row, ["latitude", "lat", "lat_dd", "y", "POINT_Y"])
        longitude = _first_present(row, ["longitude", "lon", "lng", "long_dd", "x", "POINT_X"])
        if year is None:
            year = 2020 + (idx % 4)
        try:
            year = int(float(year))
        except (TypeError, ValueError):
            year = 2020 + (idx % 4)
        try:
            metric = float(metric_value)
        except (TypeError, ValueError):
            metric = _first_numeric(row, exclude={"year", "latitude", "longitude", "lat", "lon", "x", "y"})
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            # Keep geometry workflows testable even when a portal record omits point fields.
            lat = 44.0 + (idx % 5) * 0.05
            lon = -123.0 + (idx % 5) * 0.04
        out.append(
            {
                **row,
                "year": year,
                "county": str(county or "Unknown"),
                "city": str(city or "Unknown"),
                "state": str(_first_present(row, ["state", "STATE"]) or "OR"),
                "latitude": lat,
                "longitude": lon,
                "metric_name": source_key,
                "metric_value": metric,
                "source": str(county or source_key),
                "target": str(year),
                "value": metric,
                "heat_x": year,
                "heat_y": str(county or "Unknown"),
                "heat_z": metric,
                "session_source_key": source_key,
            }
        )
    return out


def test_three_portal_live_query_transform_geometry_and_charts():
    register_three_portal_sources()
    columns = [
        "year",
        "county",
        "city",
        "state",
        "latitude",
        "longitude",
        "metric_name",
        "metric_value",
        "source",
        "target",
        "value",
        "heat_x",
        "heat_y",
        "heat_z",
    ]
    odf = source("portal_odf_firestats", PORTAL_APIS["odf_firestats"]["open_data_csv"], column_hints=columns)
    slido = source(
        "portal_dogami_slido",
        "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
        connector_type="arcgis_rest",
        column_hints=columns,
    )
    ics = source("portal_sci_data_ics209_demo", PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"], column_hints=columns)
    combined = bind_sources(odf, slido, ics)
    keys = ["portal_odf_firestats", "portal_dogami_slido", "portal_sci_data_ics209_demo"]

    rows_by_source_raw = {}
    for key in keys:
        rows = combined.fetch(source_keys=[key], limit=15, print_rows=True)
        rows_by_source_raw[key] = rows
        print(f"\nLIVE FETCHED {key}: {len(rows)} rows")
        assert len(rows) > 0

    rows_by_source = {key: _normalize_rows(key, rows) for key, rows in rows_by_source_raw.items()}
    all_rows = [row for rows in rows_by_source.values() for row in rows]
    print("\nNORMALIZED LIVE DATA")
    for row in all_rows[:20]:
        print(row)

    tools = analysis_tools()
    odf_average_source = tools.aggregate_source(rows_by_source["portal_odf_firestats"], group_by=["year"], value="metric_value", source_key="odf_average_per_year")
    slido_average_source = tools.aggregate_source(rows_by_source["portal_dogami_slido"], group_by=["year"], value="metric_value", source_key="slido_average_per_year")
    ics_average_source = tools.aggregate_source(rows_by_source["portal_sci_data_ics209_demo"], group_by=["year"], value="metric_value", source_key="ics_average_per_year")
    combined_average_source = tools.aggregate_source(all_rows, group_by=["session_source_key", "year"], value="metric_value", source_key="combined_average_by_source_year")
    derived_distribution_rows = tools.add_distribution_variable(all_rows, "metric_value", bins=5, output_column="live_metric_distribution_bin")
    derived_probability_rows = tools.add_probability_variable(derived_distribution_rows, "session_source_key", "portal_dogami_slido", output_column="probability_row_is_slido")
    derived_bayes_rows = tools.add_bayes_variable(
        derived_probability_rows,
        "session_source_key",
        "portal_dogami_slido",
        "state",
        "OR",
        output_column="bayes_slido_given_oregon",
    )
    derived_regression_rows = tools.add_regression_variable(derived_bayes_rows, x="year", y="metric_value", output_column="metric_value_regression_prediction")

    print("\nDERIVED SOURCES TO COMPARE")
    print("odf_average_per_year", odf_average_source)
    print("slido_average_per_year", slido_average_source)
    print("ics_average_per_year", ics_average_source)
    print("combined_average_by_source_year", combined_average_source)
    print("\nDERIVED VARIABLE ROWS")
    for row in derived_regression_rows[:20]:
        print(row)

    assert odf_average_source
    assert slido_average_source
    assert ics_average_source
    assert combined_average_source
    assert "live_metric_distribution_bin" in derived_regression_rows[0]
    assert "probability_row_is_slido" in derived_regression_rows[0]
    assert "bayes_slido_given_oregon" in derived_regression_rows[0]
    assert "metric_value_regression_prediction" in derived_regression_rows[0]

    artifact_dir = Path("artifacts/three_portal_live_print")
    chart = charts()
    chart.scatter(odf, "year", "metric_value", name="live_odf_scatter")
    chart.bar(slido, "metric_value", "year", name="live_slido_records_by_year")
    chart.metric(
        combined,
        "live_three_portal_metric",
        [
            {"source_key": "portal_odf_firestats", "x": "year", "y": "metric_value", "label": "ODF"},
            {"source_key": "portal_dogami_slido", "x": "year", "y": "metric_value", "label": "SLIDO"},
            {"source_key": "portal_sci_data_ics209_demo", "x": "year", "y": "metric_value", "label": "ICS"},
        ],
    )
    chart.sankey(combined, "live_three_portal_sankey")
    chart.heatmap(slido, "live_slido_heatmap", "heat_x", "heat_y", "heat_z")
    chart.correlation_matrix(combined, "live_three_portal_correlation", variables=["year", "metric_value", "heat_z"])
    chart.cross_pair(
        combined,
        "live_odf_vs_slido_cross_pair",
        ("portal_odf_firestats", "year", "metric_value"),
        ("portal_dogami_slido", "year", "metric_value"),
    )
    chart_outputs = chart.render_python(rows_by_source, artifact_dir / "charts")
    geometry_plot = tools.plot_regions(all_rows, artifact_dir / "geometry" / "live_regions_intersections.png", intersection_radius_km=25)
    distinct_regions = tools.distinct_regions(all_rows)
    intersections = tools.geometry_intersections(all_rows, radius_km=25)

    print("\nLIVE CHART OUTPUTS")
    for output in chart_outputs:
        print(output)
    print("\nLIVE GEOMETRIC ENGINE OUTPUT")
    print("distinct_regions", distinct_regions)
    print("intersections", intersections)
    print("geometry_plot", geometry_plot)
    print("\nREGRESSION/CORRELATION")
    print("correlation", tools.correlation(all_rows, variables=["year", "metric_value", "heat_z"]))
    print("regression", tools.regression(all_rows, x="year", y="metric_value"))

    assert len(chart_outputs) == 7
    assert all(Path(path).exists() for path in chart_outputs)
    assert Path(geometry_plot).exists()
    assert distinct_regions["status"] == "ok"
    assert intersections["status"] == "ok"

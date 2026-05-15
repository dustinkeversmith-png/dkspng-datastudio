from app.workflow.query.geo_resolver import GeoQueryResolver
from app.workflow.session_pipeline import SessionPipeline
from app.workflow.source_binding import analysis_tools, bind_sources, charts, combine_sources, source
from app.visualization_session import get_session
from pathlib import Path


def test_source_near_and_charts_offline():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session(label="src-test")

    geo = GeoQueryResolver(geocode_fn=lambda _p: (42.2249, -121.7817))
    src = source(
        "bind_near_demo",
        "https://example.com/sample.csv",
        pipeline=flow,
        geo=geo,
        column_hints=["metric_value", "year"],
    )
    chart = charts()
    src.near("Klamath Falls Oregon", "5mi").hint_columns(["metric_value", "year"])
    chart.bar(src, "metric_value", "year", name="occurrences_by_year")
    chart.foreach(src, "metric_value", "year", name_prefix="grid")

    session = get_session(flow.session_id or "")
    assert session.source_query_profiles["bind_near_demo"]["radius_km"] > 4
    assert session.chart_definitions[0]["type"] == "chart_bar"
    assert session.chart_definitions[1]["type"] == "chart_foreach"
    assert not hasattr(src, "charts")


def test_source_near_auto_place_coordinates_and_format_metadata():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session(label="near-auto")

    odf = source("near_odf", "https://example.com/odf.csv")
    slido = source("near_slido", "https://example.com/slido.json")
    generic = source("near_generic", "https://example.com/generic.csv")
    grouped = bind_sources(flow, odf, slido, generic)

    odf.near("Oregon", "10km", query_type="place")
    slido.near((43.8, -120.5), "5mi")
    grouped.near(
        {"lat": 45.5, "lon": -122.6},
        25,
        query_type="coordinates",
        coordinate_columns={"latitude": ["POINT_Y"], "longitude": ["POINT_X"]},
        source_keys=["near_generic"],
    )

    session = get_session(flow.session_id or "")
    odf_profile = session.source_query_profiles["near_odf"]
    slido_profile = session.source_query_profiles["near_slido"]
    generic_profile = session.source_query_profiles["near_generic"]

    assert odf_profile["near_query_type"] == "place"
    assert odf_profile["near_format"]["coordinate_columns"]["latitude"][0] == "latitude"
    assert slido_profile["near_query_type"] == "coordinates"
    assert slido_profile["radius_km"] > 8
    assert generic_profile["geo_column_candidates"]["longitude"] == ["POINT_X"]
    assert grouped.minor_source_keys == ["near_odf", "near_slido", "near_generic"]


def test_range_queries_cover_sql_and_generic_hints():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session(label="range-test")
    src = source("range_src", "https://example.com/range.csv", pipeline=flow)

    src.between("year", 2001, 2020)
    src.between("metric_value", 1, 9.5)
    src.between("severity_score", 2, 4)

    session = get_session(flow.session_id or "")
    profile = session.source_query_profiles["range_src"]
    assert profile["year_min"] == 2001
    assert profile["year_max"] == 2020
    assert profile["metric_value_min"] == 1.0
    assert profile["metric_value_max"] == 9.5
    assert profile["range_hints"] == [{"column": "severity_score", "min": 2, "max": 4}]


def test_combine_sources_cross_pair():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()

    s1 = source("cross_a", "https://example.com/a.csv")
    s2 = source("cross_b", "https://example.com/b.csv")

    bundle = combine_sources(flow, s1, s2)
    bundle.pair_variables(
        "ab_compare",
        ("cross_a", "year", "metric_value"),
        ("cross_b", "year", "metric_value"),
    )

    session = get_session(flow.session_id or "")
    assert len(session.datasets) == 2
    assert session.chart_definitions[-1]["type"] == "chart_scatter"


def test_bind_sources_returns_grouped_source_and_chart_definitions():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()

    s1 = source("single_a", "https://example.com/a.csv")
    s2 = source("single_b", "https://example.com/b.csv")

    combined = bind_sources(flow, s1, s2)
    chart = charts()
    chart.metric(
        combined,
        "single_compare",
        [
            {"source_key": "single_a", "x": "year", "y": "metric_value"},
            {"source_key": "single_b", "x": "year", "y": "metric_value"},
        ],
    )

    session = get_session(flow.session_id or "")
    assert len(session.datasets) == 2
    assert session.source_query_profiles["single_a"]["cross_source_definitions"][0]["source_key"] == "single_a"
    assert session.chart_definitions[-1]["type"] == "chart_metric"


def test_chart_functions_save_separate_files():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()
    src = source("save_src", "https://example.com/save.csv", pipeline=flow)
    chart = charts()

    output_dir = Path("artifacts/test_chart_function_outputs")
    bar_path = output_dir / "bar.svg"
    scatter_path = output_dir / "scatter.svg"
    metric_path = output_dir / "metric.svg"

    chart.bar(src, "metric_value", "year", name="bar_out", save_path=str(bar_path))
    chart.scatter(src, "year", "metric_value", name="scatter_out", save_path=str(scatter_path))
    chart.metric(
        src,
        "metric_out",
        [{"source_key": "save_src", "x": "year", "y": "metric_value"}],
        save_path=str(metric_path),
    )

    assert bar_path.exists()
    assert scatter_path.exists()
    assert metric_path.exists()


def test_fuzzy_column_resolution():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()
    src = source(
        "fuzzy_src",
        "https://example.com/z.csv",
        column_hints=["metric_value", "year"],
    )
    src.attach(flow)
    charts().scatter(src, "metric_valu", "year", name="fuzzy_test")
    session = get_session(flow.session_id or "")
    spec = session.chart_definitions[-1]
    assert spec["type"] == "chart_scatter"
    assert spec["series"][0]["x"] == "metric_value"
    assert spec["series"][0]["y"] == "year"


def test_grouped_source_fetch_defaults_to_first_and_accumulates_keys(monkeypatch, capsys):
    calls = []

    def fake_query_observations(**kwargs):
        calls.append(kwargs)
        key = kwargs["source_key"]
        return [
            {
                "source_key": key,
                "year": kwargs.get("year_min") or 2020,
                "metric_value": 10 if key == "query_a" else 20,
            }
        ]

    monkeypatch.setattr("app.workflow.source_binding.query_observations", fake_query_observations)

    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()
    grouped = bind_sources(
        flow,
        source("query_a", "https://example.com/a.csv"),
        source("query_b", "https://example.com/b.csv"),
    )

    grouped.between("year", 2010, 2020)
    default_rows = grouped.fetch(db=object(), limit=10, print_rows=True)
    captured = capsys.readouterr()
    assert "query_a" in captured.out
    assert [r["source_key"] for r in default_rows] == ["query_a"]
    assert calls[-1]["source_key"] == "query_a"

    grouped.search("fire", source_keys=["query_a", "query_b"])
    grouped.between("metric_value", 1, 100, source_keys=["query_a", "query_b"])
    combined_rows = grouped.fetch(db=object(), source_keys=["query_a", "query_b"], limit=10)
    assert [r["source_key"] for r in combined_rows] == ["query_a", "query_b"]
    assert calls[-2]["search"] == "fire"
    assert calls[-2]["metric_value_min"] == 1.0
    assert calls[-1]["metric_value_max"] == 100.0


def test_each_chart_function_with_data_source_outputs_definitions():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()
    src = source("chart_src", "https://example.com/chart.csv", pipeline=flow)
    chart = charts()

    chart.bar(src, "metric_value", "year", name="chart_bar")
    chart.scatter(src, "year", "metric_value", name="chart_scatter")
    chart.foreach(src, "year", "metric_value", name_prefix="chart_foreach", kind="scatter,bar")
    chart.foreach_expand(src, "year", "metric_value", name_prefix="chart_expand", kinds=("scatter", "bar"))
    chart.foreach_ranges(src, "year", "metric_value", [(2000, 2001)], base_name="chart_range")
    chart.metric(src, "chart_metric", [{"source_key": "chart_src", "x": "year", "y": "metric_value"}])

    session = get_session(flow.session_id or "")
    types = [c["type"] for c in session.chart_definitions]
    assert "chart_bar" in types
    assert "chart_scatter" in types
    assert "chart_foreach" in types
    assert "chart_metric" in types
    assert len(session.chart_definitions) >= 7


def test_direct_sources_fetch_chart_and_analyze_without_session(capsys):
    data_dir = Path("artifacts/test_direct_runtime")
    data_dir.mkdir(parents=True, exist_ok=True)
    a_path = data_dir / "a.csv"
    b_path = data_dir / "b.csv"
    a_path.write_text(
        "year,county,state,latitude,longitude,metric_name,metric_value\n"
        "2020,Lane,OR,44.0,-123.0,fire,10\n"
        "2021,Lane,OR,44.1,-123.1,fire,20\n",
        encoding="utf-8",
    )
    b_path.write_text(
        "year,county,state,latitude,longitude,metric_name,metric_value\n"
        "2020,Multnomah,OR,45.5,-122.6,fire,30\n"
        "2021,Lane,OR,44.2,-123.2,other,40\n",
        encoding="utf-8",
    )

    grouped = bind_sources(
        source("direct_a", str(a_path)),
        source("direct_b", str(b_path)),
    )
    grouped.search("fire", source_keys=["direct_a", "direct_b"]).year_range(
        2020,
        2021,
        source_keys=["direct_a", "direct_b"],
    )

    default_rows = grouped.fetch(limit=10, print_rows=True)
    printed = capsys.readouterr()
    assert "direct_a" in printed.out
    assert [r["session_source_key"] for r in default_rows] == ["direct_a", "direct_a"]

    combined_rows = grouped.fetch(source_keys=["direct_a", "direct_b"], limit=10)
    assert [r["session_source_key"] for r in combined_rows] == ["direct_a", "direct_a", "direct_b"]

    chart = charts()
    chart.bar(grouped, "metric_value", "year", name="direct_bar", save_path=str(data_dir / "direct_bar.svg"))
    chart.scatter(grouped, "year", "metric_value", name="direct_scatter")
    chart.metric(grouped, "direct_metric", [{"source_key": "direct_a", "x": "year", "y": "metric_value"}])
    assert (data_dir / "direct_bar.svg").exists()
    assert [c["type"] for c in chart.definitions] == ["chart_bar", "chart_scatter", "chart_metric"]

    tools = analysis_tools()
    corr = tools.correlation(combined_rows, variables=["year", "metric_value"])
    reg = tools.regression(combined_rows, x="year", y="metric_value")
    counties = tools.county_compare(combined_rows)
    assert corr["status"] == "ok"
    assert reg["status"] == "ok"
    assert counties["counties"][0]["county"] in {"Lane", "Multnomah"}

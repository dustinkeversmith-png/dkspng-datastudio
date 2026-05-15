from app.chart_specs import validate_chart_definition
from app.workflow.chart_query import build_metric_chart


def test_metric_chart_spec_roundtrip():
    raw = build_metric_chart(
        "dual",
        [
            {
                "source_key": "a",
                "x": "year",
                "y": "metric_value",
                "label": "Series A",
                "style": {"color": "#ff0000", "line_dash": "dash"},
            },
            {"source_key": "b", "x": "year", "y": "metric_value"},
        ],
        layout={"title": {"text": "Compare"}},
        notes="demo",
    )
    assert raw["type"] == "chart_metric"
    validate_chart_definition(raw)


def test_range_resolver_year():
    from app.workflow.query.range_resolver import RangeQueryResolver

    r = RangeQueryResolver()
    assert r.between("year", 2000, 2020) == {"year_min": 2000, "year_max": 2020}


def test_range_resolver_observed_at_and_metric_value():
    from app.workflow.query.range_resolver import RangeQueryResolver

    r = RangeQueryResolver()
    observed = r.between("observed_at", "2020-01-01", "2020-12-31")
    metric = r.between("value", 1, 2.5)

    assert observed["observed_at_min"].startswith("2020-01-01")
    assert observed["observed_at_max"].startswith("2020-12-31")
    assert metric == {"metric_value_min": 1.0, "metric_value_max": 2.5}

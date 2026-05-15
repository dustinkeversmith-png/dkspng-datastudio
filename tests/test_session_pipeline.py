"""SessionPipeline workflow and scoped pipeline behavior."""

from app.data_manipulation import apply_pipeline
from app.workflow.data_reshape import DataReshaper
from app.workflow.session_pipeline import ColumnResolver, SessionPipeline


def test_reference_scope_limits_exclude():
    rows = [
        {"session_dataset_id": "a", "session_source_key": "src_a", "x": 1, "noise": 9},
        {"session_dataset_id": "b", "session_source_key": "src_b", "x": 2, "noise": 8},
    ]
    steps = [
        {"type": "reference_scope", "source_keys": ["src_a"], "mode": "replace"},
        {"type": "exclude_columns", "columns": ["noise"]},
    ]
    out = apply_pipeline(rows, steps)
    assert out[0] == {"session_dataset_id": "a", "session_source_key": "src_a", "x": 1}
    assert "noise" in out[1]


def test_exclude_rows_by_index():
    rows = [{"session_dataset_id": "a", "k": i} for i in range(5)]
    steps = [{"type": "exclude_rows", "indices": [1, 3]}]
    out = apply_pipeline(rows, steps)
    assert [r["k"] for r in out] == [0, 2, 4]


def test_stack_columns():
    rows = [
        {"session_dataset_id": "d", "year": 2020, "a": 1.0, "b": 2.0},
    ]
    steps = [
        {
            "type": "stack_columns",
            "id_vars": ["year", "session_dataset_id"],
            "measure_vars": ["a", "b"],
            "var_name": "metric",
            "value_name": "val",
        }
    ]
    out = apply_pipeline(rows, steps)
    assert len(out) == 2
    metrics = sorted(r["metric"] for r in out)
    assert metrics == ["a", "b"]


def test_session_pipeline_registers_source_and_buffer():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session(label="test")
    sid = flow.session_id
    assert sid

    flow.add_source(
        "pipeline_test_src",
        "https://example.com/data.csv",
        display_name="Pipeline test",
    )
    flow.reference("pipeline_test_src")
    flow.exclude_columns("raw_properties_json")
    flow.scatter_chart("demo", [("pipeline_test_src", "longitude", "latitude")])

    from app.visualization_session import get_session

    s = get_session(sid)
    assert len(s.command_buffer) == 2
    assert s.command_buffer[0]["type"] == "reference_scope"
    assert len(s.chart_definitions) == 1
    assert s.chart_definitions[0]["type"] == "chart_scatter"

    flow.save_snapshot("v1", notes="checkpoint")
    s2 = get_session(sid)
    assert len(s2.saved_snapshots) == 1
    assert s2.saved_snapshots[0]["name"] == "v1"
    assert "buffer" in s2.saved_snapshots[0]


def test_column_resolver_numeric():
    r = ColumnResolver(names=["a", "b", "c"])
    assert r.resolve_all([0, "2"]) == ["a", "c"]


def test_data_reshaper_delegates():
    flow = SessionPipeline(discard_previous_on_new=False)
    flow.new_session()
    flow.add_source("reshape_src", "https://example.com/x.csv")
    reshaper = DataReshaper(flow)
    reshaper.melt(["year"], ["v1", "v2"])
    from app.visualization_session import get_session

    s = get_session(flow.session_id or "")
    assert s.command_buffer[-1]["type"] == "stack_columns"

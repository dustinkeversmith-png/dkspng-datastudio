from app.chart_specs import validate_chart_definition
from app.workflow.chart_foreach_expand import expand_pair_grid, materialize_foreach_spec


def test_expand_pair_grid_both_kinds():
    charts = expand_pair_grid(
        "src_a",
        ["year"],
        ["metric_value", "county"],
        kinds=("scatter", "bar"),
        name_prefix="t",
    )
    assert len(charts) == 4  # 2 pairs × 2 kinds
    types = {c["type"] for c in charts}
    assert types == {"chart_scatter", "chart_bar"}
    for c in charts:
        validate_chart_definition(c)


def test_materialize_foreach_spec_legacy_chart_kind():
    raw = {
        "type": "chart_foreach",
        "name_prefix": "p",
        "source_key": "s",
        "x_columns": ["a"],
        "y_columns": ["b"],
        "chart_kind": "scatter",
    }
    expanded = materialize_foreach_spec(raw)
    assert len(expanded) == 1

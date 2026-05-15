from app.data_manipulation import ExcludeColumnsStep, IncludeColumnsStep, JoinStep, apply_pipeline


def test_exclude_columns():
    rows = [
        {"session_dataset_id": "a", "year": 2020, "county": "X", "noise": 1},
        {"session_dataset_id": "b", "year": 2021, "noise": 2},
    ]
    out = apply_pipeline(rows, [ExcludeColumnsStep(columns=["noise"]).model_dump()])
    assert "noise" not in out[0]
    assert out[0]["year"] == 2020


def test_include_columns_keeps_meta():
    rows = [{"session_dataset_id": "a", "year": 2020, "county": "Y", "extra": 9}]
    out = apply_pipeline(rows, [IncludeColumnsStep(columns=["year", "county"]).model_dump()])
    assert set(out[0].keys()) >= {"year", "county", "session_dataset_id"}
    assert "extra" not in out[0]


def test_join_inner():
    rows = [
        {"session_dataset_id": "L", "county": "A", "v": 1},
        {"session_dataset_id": "R", "county": "A", "w": 2},
    ]
    steps = [
        JoinStep(
            left_dataset_id="L",
            right_dataset_id="R",
            on=["county"],
            how="inner",
        ).model_dump()
    ]
    out = apply_pipeline(rows, steps)
    assert len(out) == 1
    assert out[0]["county"] == "A"


def test_pipeline_dict_validation():
    rows = [{"x": 1}]
    out = apply_pipeline(rows, [{"type": "exclude_columns", "columns": ["x"]}])
    assert out == [{}]

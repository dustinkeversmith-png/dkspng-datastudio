from app.core.lineage import create_lineage_record, append_lineage

def test_create_lineage_record():
    record = create_lineage_record(
        parent_source_key="base_fire_source",
        operation_key="filter_op",
        params={"acres_burned_gt": 10}
    )
    
    assert "record_id" in record
    assert "timestamp" in record
    assert record["parent_source_key"] == "base_fire_source"
    assert record["operation_key"] == "filter_op"
    assert record["params"]["acres_burned_gt"] == 10

def test_append_lineage():
    existing = {
        "history": [
            {"operation_key": "select_op"}
        ]
    }
    
    new_record = create_lineage_record("test", "rename_op", {})
    
    updated = append_lineage(existing, new_record)
    assert len(updated["history"]) == 2
    assert updated["history"][0]["operation_key"] == "select_op"
    assert updated["history"][1]["operation_key"] == "rename_op"

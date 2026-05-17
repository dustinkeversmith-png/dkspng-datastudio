import pytest
import pandas as pd
from app.workflow.source_binding import source
from app.schemas import SourceDefinition
from app.core.selectors import select_source_dataframe

@pytest.fixture
def fire_source():
    definition = SourceDefinition(
        source_key="test_fire_occurrences",
        display_name="Test Fire Occurrences",
        category="test",
        connector_type="csv",
        source_url="tests/fixtures/sources/fire_occurrences.csv"
    )
    return source(definition)

def test_select_source_dataframe(fire_source):
    df = select_source_dataframe(fire_source)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 4
    assert "incident_id" in df.columns
    assert "acres_burned" in df.columns

def test_select_source_dataframe_with_limit(fire_source):
    df = select_source_dataframe(fire_source, limit=2)
    assert len(df) == 2

def test_select_source_dataframe_specific_key(fire_source):
    df = select_source_dataframe(fire_source, source_key="test_fire_occurrences")
    assert not df.empty
    assert df["session_source_key"].iloc[0] == "test_fire_occurrences"

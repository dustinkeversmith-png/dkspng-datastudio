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

import json
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

    # Take the multi source get the metadata
    s.generate_metadata()

    # export the metadata to a json file
    with open("tests/fixtures/metadata.json", "w") as f:
        json.dump(s.metadata, f, indent=4)

    # read the metadata from the json file
    with open("tests/fixtures/metadata.json", "r") as f:
        metadata = json.load(f)




    
    


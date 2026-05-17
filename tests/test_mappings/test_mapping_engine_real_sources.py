import pytest
from app.core.context import ExecutionContext
from app.workflow.source_binding import source
from app.schemas import SourceDefinition
from app.mappings.mapping_targets import MappingTarget, ResolvedMapping
from app.mappings.base_mapping import BaseMapping
from app.mappings.mapping_engine import MappingEngine

class MockRealSourceMapping(BaseMapping):
    @property
    def mapping_key(self) -> str:
        return "mock_real_source_mapping"
        
    @property
    def display_name(self) -> str:
        return "Mock Real Source Mapping"
        
    def resolve(self, context: ExecutionContext) -> ResolvedMapping:
        # Build semantic targets directly
        target_lat = MappingTarget(
            target_key="latitude_field",
            target_type="field",
            selector={"name": "latitude"},
            role="spatial_y"
        )
        target_lon = MappingTarget(
            target_key="longitude_field",
            target_type="field",
            selector={"name": "longitude"},
            role="spatial_x"
        )
        target_dataset = MappingTarget(
            target_key="entire_dataset",
            target_type="dataset",
            selector={"all": True},
            role="source_data"
        )
        
        return ResolvedMapping(
            mapping_key=self.mapping_key,
            targets={
                "latitude_field": target_lat,
                "longitude_field": target_lon,
                "entire_dataset": target_dataset
            },
            source_key=context.source_key
        )


@pytest.fixture
def fire_context():
    definition = SourceDefinition(
        source_key="test_fire_occurrences",
        display_name="Test Fire Occurrences",
        category="test",
        connector_type="csv",
        source_url="tests/fixtures/sources/fire_occurrences.csv"
    )
    return ExecutionContext(source=source(definition), source_key="test_fire_occurrences")

def test_mapping_engine_resolves_targets(fire_context):
    engine = MappingEngine()
    mapping = MockRealSourceMapping()
    
    resolved = engine.execute_mapping(mapping, fire_context)
    
    assert resolved.mapping_key == "mock_real_source_mapping"
    assert len(resolved.targets) == 3
    
    # Test by_type
    fields = resolved.by_type("field")
    assert len(fields) == 2
    
    datasets = resolved.by_type("dataset")
    assert len(datasets) == 1
    
    # Test by_role
    lat = resolved.by_role("spatial_y")
    assert len(lat) == 1
    assert lat[0].selector["name"] == "latitude"
    
    # Test get
    lon = resolved.get("longitude_field")
    assert lon.role == "spatial_x"

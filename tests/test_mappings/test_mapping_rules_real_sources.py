import pytest
from app.core.context import ExecutionContext
from app.mappings.mapping_targets import MappingTarget
from app.mappings.rules.concrete_rules import RenameRule, SemanticRoleRule, GeometryRoleRule, TypeRoleRule
from app.mappings.mapping_engine import MappingEngine

@pytest.fixture
def dummy_context():
    return ExecutionContext(source=None)

def test_rename_rule(dummy_context):
    target = MappingTarget(
        target_key="raw_date",
        target_type="field",
        selector={"name": "FIRE_DATE"}
    )
    rule = RenameRule("incident_date")
    engine = MappingEngine()
    
    result = engine.apply_rules_to_target(target, [rule], dummy_context)
    assert result.display_name == "incident_date"
    assert result.selector["name"] == "FIRE_DATE"

def test_geometry_role_rule(dummy_context):
    target = MappingTarget(
        target_key="fire_points",
        target_type="point_data",
        selector={"lat": "latitude", "lon": "longitude"}
    )
    rule = GeometryRoleRule()
    engine = MappingEngine()
    
    result = engine.apply_rules_to_target(target, [rule], dummy_context)
    assert result.role == "spatial_geometry"
    assert result.target_type == "geometry"

def test_semantic_role_rule(dummy_context):
    target = MappingTarget(
        target_key="county_field",
        target_type="field",
        selector={"name": "county"}
    )
    rule = SemanticRoleRule("administrative_boundary")
    engine = MappingEngine()
    
    result = engine.apply_rules_to_target(target, [rule], dummy_context)
    assert result.role == "administrative_boundary"

def test_type_role_rule(dummy_context):
    target = MappingTarget(
        target_key="acres_burned",
        target_type="field",
        selector={"name": "acres_burned"}
    )
    rule = TypeRoleRule("numeric")
    engine = MappingEngine()
    
    result = engine.apply_rules_to_target(target, [rule], dummy_context)
    assert result.semantic_type == "numeric"

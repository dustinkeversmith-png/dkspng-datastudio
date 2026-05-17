from app.mappings.rules import BaseMappingRule
from app.core.context import ExecutionContext
from app.mappings.mapping_targets import MappingTarget

class RenameRule(BaseMappingRule):
    def __init__(self, new_name: str):
        self.new_name = new_name
        
    @property
    def rule_key(self) -> str:
        return "rename_rule"
        
    def apply(self, context: ExecutionContext, target: MappingTarget) -> MappingTarget:
        target.display_name = self.new_name
        return target

class SemanticRoleRule(BaseMappingRule):
    def __init__(self, role: str):
        self.role = role

    @property
    def rule_key(self) -> str:
        return "semantic_role_rule"
        
    def apply(self, context: ExecutionContext, target: MappingTarget) -> MappingTarget:
        target.role = self.role
        return target

class GeometryRoleRule(BaseMappingRule):
    @property
    def rule_key(self) -> str:
        return "geometry_role_rule"
        
    def apply(self, context: ExecutionContext, target: MappingTarget) -> MappingTarget:
        target.role = "spatial_geometry"
        target.target_type = "geometry"
        return target

class TypeRoleRule(BaseMappingRule):
    def __init__(self, semantic_type: str):
        self.semantic_type = semantic_type

    @property
    def rule_key(self) -> str:
        return "type_role_rule"
        
    def apply(self, context: ExecutionContext, target: MappingTarget) -> MappingTarget:
        target.semantic_type = self.semantic_type
        return target

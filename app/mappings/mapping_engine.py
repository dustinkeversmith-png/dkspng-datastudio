from typing import Any, Dict, List
from app.core.context import ExecutionContext
from app.mappings.mapping_targets import MappingTarget, ResolvedMapping
from app.mappings.base_mapping import BaseMapping
from app.mappings.rules import BaseMappingRule

class MappingEngine:
    """
    Engine to orchestrate the resolution of targets and application of rules.
    """
    
    def __init__(self):
        pass
        
    def execute_mapping(self, mapping: BaseMapping, context: ExecutionContext) -> ResolvedMapping:
        """Fully resolve a mapping specification into semantic targets."""
        return mapping.resolve(context)

    def apply_rules_to_target(self, target: MappingTarget, rules: List[BaseMappingRule], context: ExecutionContext) -> MappingTarget:
        """Pass a target through a pipeline of mapping rules."""
        current_target = target
        for rule in rules:
            current_target = rule.apply(context, current_target)
        return current_target

import pytest
from app.core.component import BaseComponent
from app.core.context import ExecutionContext
from app.core.result import ComponentResult
from app.core.validation import ValidationResult
from app.workflow.source_binding import source
from app.schemas import SourceDefinition

class ValidComponent(BaseComponent):
    @property
    def component_key(self) -> str:
        return "valid_comp"
        
    @property
    def display_name(self) -> str:
        return "Valid Component"
        
    def validate(self, context: ExecutionContext) -> ValidationResult:
        if not context.source:
            return ValidationResult.failure(["No source provided"])
        return ValidationResult.success()
        
    def execute(self, context: ExecutionContext) -> ComponentResult:
        return ComponentResult(
            component_key=self.component_key,
            result_type="test_result",
            data={"status": "executed"}
        )

def test_component_contract_implementation():
    comp = ValidComponent()
    assert comp.component_key == "valid_comp"
    assert comp.display_name == "Valid Component"
    assert comp.description is None

def test_component_execution_flow():
    comp = ValidComponent()
    
    definition = SourceDefinition(
        source_key="test_fire_occurrences",
        display_name="Test Fire Occurrences",
        category="test",
        connector_type="csv",
        source_url="tests/fixtures/sources/fire_occurrences.csv"
    )
    src = source(definition)
    
    ctx = ExecutionContext(source=src)
    
    val_result = comp.validate(ctx)
    assert val_result.ok is True
    
    exec_result = comp.execute(ctx)
    assert exec_result.result_type == "test_result"
    assert exec_result.data["status"] == "executed"

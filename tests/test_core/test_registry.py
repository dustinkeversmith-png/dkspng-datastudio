import pytest
from app.core.registry import ComponentRegistry
from app.core.component import BaseComponent
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult

class DummyComponent(BaseComponent):
    @property
    def component_key(self) -> str:
        return "dummy_comp"
        
    @property
    def display_name(self) -> str:
        return "Dummy Component"
        
    def validate(self, context: ExecutionContext) -> ValidationResult:
        return ValidationResult.success()
        
    def execute(self, context: ExecutionContext) -> ComponentResult:
        return ComponentResult(component_key=self.component_key, result_type="dummy")

class AnotherComponent(BaseComponent):
    @property
    def component_key(self) -> str:
        return "another_comp"
        
    @property
    def display_name(self) -> str:
        return "Another Component"
        
    def validate(self, context: ExecutionContext) -> ValidationResult:
        return ValidationResult.success()
        
    def execute(self, context: ExecutionContext) -> ComponentResult:
        return ComponentResult(component_key=self.component_key, result_type="dummy")


def test_registry_registration_and_retrieval():
    registry = ComponentRegistry()
    comp = DummyComponent()
    
    registry.register(comp)
    assert registry.has("dummy_comp")
    
    retrieved = registry.get("dummy_comp")
    assert retrieved is comp
    assert "dummy_comp" in registry.list_keys()

def test_registry_duplicate_registration_fails():
    registry = ComponentRegistry()
    comp = DummyComponent()
    registry.register(comp)
    
    with pytest.raises(ValueError):
        registry.register(comp)

def test_registry_duplicate_registration_allowed():
    registry = ComponentRegistry()
    comp = DummyComponent()
    registry.register(comp)
    registry.register(comp, allow_duplicate=True) # Should not raise
    assert registry.has("dummy_comp")

def test_registry_missing_key_raises():
    registry = ComponentRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")

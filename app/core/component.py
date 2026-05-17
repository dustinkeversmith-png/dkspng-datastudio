from abc import ABC, abstractmethod
from typing import Optional
from app.core.context import ExecutionContext
from app.core.result import ComponentResult
from app.core.validation import ValidationResult

class BaseComponent(ABC):
    @property
    @abstractmethod
    def component_key(self) -> str:
        """Unique identifier for the component."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for the component."""
        pass

    @property
    def description(self) -> Optional[str]:
        """Optional description of the component's behavior."""
        return None

    @abstractmethod
    def validate(self, context: ExecutionContext) -> ValidationResult:
        """Validate if the component can run with the given context."""
        pass

    @abstractmethod
    def execute(self, context: ExecutionContext) -> ComponentResult:
        """Execute the component with the given context."""
        pass

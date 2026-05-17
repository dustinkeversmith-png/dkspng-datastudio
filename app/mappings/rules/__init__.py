from abc import ABC, abstractmethod
from app.core.context import ExecutionContext
from app.mappings.mapping_targets import MappingTarget

class BaseMappingRule(ABC):
    @property
    @abstractmethod
    def rule_key(self) -> str:
        pass

    @abstractmethod
    def apply(self, context: ExecutionContext, target: MappingTarget) -> MappingTarget:
        """Apply a semantic or structural rule to mutate the mapping target."""
        pass

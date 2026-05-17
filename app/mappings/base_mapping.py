from abc import ABC, abstractmethod
from app.core.context import ExecutionContext
from app.mappings.mapping_targets import ResolvedMapping

class BaseMapping(ABC):
    @property
    @abstractmethod
    def mapping_key(self) -> str:
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    @abstractmethod
    def resolve(self, context: ExecutionContext) -> ResolvedMapping:
        """Resolve the semantic mapping targets against the given execution context."""
        pass

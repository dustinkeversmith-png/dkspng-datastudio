from abc import ABC, abstractmethod
from typing import Any
from app.core.result import ComponentResult

class BaseFormatter(ABC):
    """
    Serializes a View's ComponentResult into a specific string format (JSON, CSV, HTML).
    """
    @abstractmethod
    def format(self, result: ComponentResult) -> str:
        pass

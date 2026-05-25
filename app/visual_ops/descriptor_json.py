"""VisualDescriptor — structured JSON output for the visual operator pipeline."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualDescriptor:
    """Represents the complete rendering specification for one chart."""

    plot_type: str
    data: dict[str, Any] = field(default_factory=dict)
    operators: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plot_type": self.plot_type,
            "data": self.data,
            "operators": self.operators,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def add_operator(self, op: str, **kwargs) -> "VisualDescriptor":
        entry = {"op": op}
        entry.update(kwargs)
        self.operators.append(entry)
        return self

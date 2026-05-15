"""
Future: parse rich selection DSL into structured filters + pipeline steps.

Stub keeps a stable import surface for a later tokenizer/grammar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SelectionCommandParser:
    """
    Placeholder for deeper query syntax (e.g. ``county is X and year > 2010``).

    Call :meth:`register` to attach handlers without committing to grammar yet.
    """

    _handlers: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, fn: Any) -> None:
        self._handlers[name] = fn

    def parse(self, text: str) -> dict[str, Any]:
        raise NotImplementedError(
            "Structured command parsing is not implemented yet; use Source.near / search / SessionPipeline instead."
        )

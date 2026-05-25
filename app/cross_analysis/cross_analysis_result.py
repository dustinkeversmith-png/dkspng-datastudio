"""CrossAnalysisResult — typed output from a cross-source analysis run."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from app.models.model_result import ModelResult


@dataclass
class CrossAnalysisResult:
    spec_grouping: str
    model_results: list[ModelResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_grouping": self.spec_grouping,
            "n_model_results": len(self.model_results),
            "model_results": [r.to_dict() for r in self.model_results],
            "summary": self.summary,
            "lineage": self.lineage,
        }

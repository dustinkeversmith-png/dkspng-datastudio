"""Typed result objects for sampling analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SamplingResult:
    """Unified result for any sampling operation."""

    source_key: str
    target: str | None
    method: str
    sample_size: int
    population_size: int | None = None
    statistic: str | None = None
    estimate: float | None = None
    uncertainty: float | None = None
    confidence_interval: tuple[float, float] | None = None
    bias_score: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "target": self.target,
            "method": self.method,
            "sample_size": self.sample_size,
            "population_size": self.population_size,
            "statistic": self.statistic,
            "estimate": self.estimate,
            "uncertainty": self.uncertainty,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            "bias_score": self.bias_score,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        ci = f"CI={self.confidence_interval}" if self.confidence_interval else ""
        return (
            f"SamplingResult(key={self.source_key!r}, target={self.target!r}, "
            f"method={self.method!r}, estimate={self.estimate}, {ci})"
        )

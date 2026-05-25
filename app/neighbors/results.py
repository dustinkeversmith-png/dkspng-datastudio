"""NeighborResult — typed output from KNN spatial-temporal analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NeighborResult:
    """Output of NeighborEngine.knn()."""

    source_key: str
    n_neighbors: int
    feature_fields: list[str]
    neighbor_indices: list[list[int]]      # per-row neighbor row indices
    distances: list[list[float]]           # per-row distances
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "n_neighbors": self.n_neighbors,
            "feature_fields": self.feature_fields,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"NeighborResult(key={self.source_key!r}, k={self.n_neighbors}, "
            f"features={self.feature_fields})"
        )

"""ClusterResult — typed output from KMeans spatial-temporal clustering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClusterResult:
    """Output of ClusterEngine.kmeans()."""

    cluster_key: str
    k: int
    labels: list[int]
    centers: list[list[float]]
    feature_names: list[str]
    inertia: float = 0.0
    silhouette_score: float = 0.0
    cluster_profiles: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_key": self.cluster_key,
            "k": self.k,
            "labels": self.labels,
            "centers": self.centers,
            "feature_names": self.feature_names,
            "inertia": self.inertia,
            "silhouette_score": self.silhouette_score,
            "cluster_profiles": self.cluster_profiles,
            "metrics": self.metrics,
        }

    def __repr__(self) -> str:
        return (
            f"ClusterResult(key={self.cluster_key!r}, k={self.k}, "
            f"inertia={self.inertia:.2f}, silhouette={self.silhouette_score:.3f})"
        )

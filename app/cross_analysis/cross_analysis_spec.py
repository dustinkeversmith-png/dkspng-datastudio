"""CrossAnalysisSpec — declarative description of a cross-source analysis run."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CrossAnalysisSpec:
    """Describes grouping, variable groups, and models to run.

    Example
    -------
    spec = CrossAnalysisSpec(
        grouping="kmeans_cluster",
        variable_groups={
            "weather":    ["TEMP", "GUST", "PRCP", "VISIB"],
            "air_quality": ["AQI"],
            "fire":       ["specificcause"],
            "landslide":  ["CONTR_FACT", "AREA_ft2", "VOLUME_ft3", "DEEP_SHAL"],
        },
        models=["linear_regression", "logistic_regression", "svm", "naive_bayes"],
    )
    """

    grouping: str = "kmeans_cluster"
    variable_groups: dict[str, list[str]] = field(default_factory=dict)
    models: list[str] = field(default_factory=lambda: [
        "linear_regression", "logistic_regression", "svm", "naive_bayes",
    ])
    max_features: int = 10   # cap features passed to each model

    def all_pairs(self) -> list[tuple[str, str]]:
        """Return all ordered (feature_group, target_group) pairs."""
        keys = list(self.variable_groups)
        pairs = []
        for i, a in enumerate(keys):
            for b in keys[i+1:]:
                pairs.append((a, b))
                pairs.append((b, a))
        return pairs

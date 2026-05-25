"""Typed result objects for model analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class ModelEvaluation:
    model_key: str
    task_type: str
    metrics: dict[str, Any] = field(default_factory=dict)
    uncertainty: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_key": self.model_key,
            "task_type": self.task_type,
            "metrics": self.metrics,
            "uncertainty": self.uncertainty,
        }


@dataclass
class PredictionResult:
    model_key: str
    predictions: list[Any] = field(default_factory=list)
    prediction_intervals: list[tuple[float, float]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_key": self.model_key,
            "n_predictions": len(self.predictions),
            "metadata": self.metadata,
        }


@dataclass
class ModelResult:
    """Unified output from any model fit + evaluate cycle."""

    model_key: str
    task_type: str
    source_key: str
    feature_fields: list[str]
    target_field: str | None
    metrics: dict[str, Any] = field(default_factory=dict)
    uncertainty: dict[str, Any] = field(default_factory=dict)
    predictions: list[Any] = field(default_factory=list)
    chart_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)
    fitted_model_ref: Any = field(default=None, repr=False)
    points: pd.DataFrame = field(default_factory=pd.DataFrame, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_key": self.model_key,
            "task_type": self.task_type,
            "source_key": self.source_key,
            "feature_fields": self.feature_fields,
            "target_field": self.target_field,
            "metrics": self.metrics,
            "uncertainty": self.uncertainty,
            "chart_paths": self.chart_paths,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    def __repr__(self) -> str:
        return (
            f"ModelResult(model={self.model_key!r}, source={self.source_key!r}, "
            f"target={self.target_field!r}, metrics={self.metrics})"
        )

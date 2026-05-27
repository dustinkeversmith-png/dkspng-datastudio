"""Linear regression model."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult

@dataclass
class RegressionResult:
    """Result of Source.log_regression()."""
    weights: list[float]
    bias: float
    r2: float
    feature_cols: list[str]
    target_col: str
    points: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self) -> str:
        return (
            f"RegressionResult(r2={self.r2:.4f}, "
            f"weights={self.weights}, bias={self.bias:.4f})"
        )




@register_model
class LinearRegressionModel(BaseModel):
    model_key = "linear_regression"
    task_type = "regression"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None
        fitted = None

        try:
            from sklearn.linear_model import LinearRegression
            import numpy as np

            model = LinearRegression()
            model.fit(X, y)
            fitted = model

            preds = model.predict(X)
            residuals = y.values - preds
            ss_res = float(np.sum(residuals ** 2))
            ss_tot = float(np.sum((y.values - y.mean()) ** 2))
            r2 = 1 - ss_res / (ss_tot + 1e-9)
            mae = float(np.mean(np.abs(residuals)))
            mse = float(np.mean(residuals ** 2))
            rmse = float(np.sqrt(mse))

            metrics = {"r2": round(r2, 4), "mae": round(mae, 4), "mse": round(mse, 4), "rmse": round(rmse, 4)}
            uncertainty = {"prediction_interval_approx": round(2 * rmse, 4),
                           "residual_std": round(float(np.std(residuals)), 4)}

            return ModelResult(
                model_key=self.model_key,
                task_type=self.task_type,
                source_key=source_key,
                feature_fields=list(X.columns),
                target_field=target,
                metrics=metrics,
                uncertainty=uncertainty,
                predictions=preds.tolist(),
                fitted_model_ref=fitted,
                lineage={"coef": model.coef_.tolist(), "intercept": float(model.intercept_)},
            )
        except ImportError:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target,
                metadata={"warning": "sklearn not available"},
            )

    def predict(self, X: pd.DataFrame, context: dict[str, Any]) -> PredictionResult:
        return PredictionResult(model_key=self.model_key)

    def evaluate(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelEvaluation:
        return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

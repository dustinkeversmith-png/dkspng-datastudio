"""Linear regression model."""
from __future__ import annotations
from typing import Any

import pandas as pd

from app.models.base_model import BaseModel, register_model
from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation


@register_model
class LinearRegressionModel(BaseModel):
    model_key = "linear_regression"
    task_type = "regression"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None
        metrics: dict[str, Any] = {}
        chart_paths: list[str] = []
        fitted = None

        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import cross_val_score
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

            metrics = {"r2": round(r2, 4), "mae": round(mae, 4),
                       "mse": round(mse, 4), "rmse": round(rmse, 4)}

            # Prediction interval (approx: ±2*RMSE)
            uncertainty = {"prediction_interval_approx": round(2 * rmse, 4),
                           "residual_std": round(float(np.std(residuals)), 4)}

            # Chart
            if context.get("plot"):
                chart_paths = self._plot(X, y, preds, residuals,
                                         source_key, context["plot_dir"])

            return ModelResult(
                model_key=self.model_key,
                task_type=self.task_type,
                source_key=source_key,
                feature_fields=list(X.columns),
                target_field=target,
                metrics=metrics,
                uncertainty=uncertainty,
                predictions=preds.tolist(),
                chart_paths=chart_paths,
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

    @staticmethod
    def _plot(X, y, preds, residuals, source_key, plot_dir) -> list[str]:
        paths: list[str] = []
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
            import os

            feat = X.columns[0]

            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            axes[0].scatter(X[feat], y, alpha=0.5, label="Data", s=15)
            axes[0].scatter(X[feat], preds, alpha=0.5, color="tomato", s=10, label="Fit")
            axes[0].set_xlabel(feat); axes[0].set_ylabel(str(y.name))
            axes[0].set_title(f"Linear Regression — {source_key}"); axes[0].legend()

            axes[1].scatter(preds, residuals, alpha=0.5, s=15)
            axes[1].axhline(0, color="tomato", lw=1)
            axes[1].set_xlabel("Fitted"); axes[1].set_ylabel("Residual")
            axes[1].set_title("Residual Plot")

            plt.tight_layout()
            path = os.path.join(plot_dir, f"linreg_{source_key}.png")
            plt.savefig(path, dpi=90); plt.close(fig)
            paths.append(path)
        except Exception:
            pass
        return paths

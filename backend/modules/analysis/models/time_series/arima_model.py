"""ARIMA time-series model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class ARIMAModel(BaseModel):
    model_key = "arima"
    task_type = "time_series"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else (X.columns[0] if not X.empty else None)
        forecast_steps = context.get("forecast_steps", 10)
        order = context.get("arima_order", (1, 1, 1))
        series = y if y is not None else X.iloc[:, 0]

        try:
            from statsmodels.tsa.arima.model import ARIMA
            import numpy as np, warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(series.values, order=order)
                fit = model.fit()

            forecast = fit.forecast(steps=forecast_steps)
            conf_int = fit.get_forecast(steps=forecast_steps).conf_int().tolist()
            residuals = fit.resid.tolist()
            aic = float(fit.aic)
            bic = float(fit.bic)
            rmse = float(np.sqrt(np.mean(np.array(residuals)**2)))

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metrics={"aic": round(aic,2), "bic": round(bic,2), "rmse": round(rmse,4)},
                uncertainty={"forecast_conf_int": conf_int[:3]},
                predictions=forecast.tolist(),
                fitted_model_ref=fit,
                lineage={"order": list(order)},
            )
        except ImportError:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metadata={"warning": "statsmodels not available — ARIMA skipped"},
            )
        except Exception as e:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metadata={"warning": f"ARIMA failed: {e}"},
            )

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

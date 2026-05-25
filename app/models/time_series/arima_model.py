"""ARIMA time-series model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from app.models.base_model import BaseModel, register_model
from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation


@register_model
class ARIMAModel(BaseModel):
    model_key = "arima"
    task_type = "time_series"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else (X.columns[0] if not X.empty else None)
        forecast_steps = context.get("forecast_steps", 10)
        order = context.get("arima_order", (1, 1, 1))
        chart_paths: list[str] = []
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

            if context.get("plot"):
                chart_paths = self._plot(series, forecast, conf_int, source_key, context["plot_dir"])

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metrics={"aic": round(aic,2), "bic": round(bic,2), "rmse": round(rmse,4)},
                uncertainty={"forecast_conf_int": conf_int[:3]},
                predictions=forecast.tolist(),
                chart_paths=chart_paths, fitted_model_ref=fit,
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

    @staticmethod
    def _plot(series, forecast, conf_int, source_key, plot_dir) -> list[str]:
        paths: list[str] = []
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt, os, numpy as np
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(range(len(series)), series.values, label="Observed", color="#5b8db8")
            fc_x = range(len(series), len(series)+len(forecast))
            ax.plot(fc_x, forecast, label="Forecast", color="tomato")
            lo = [c[0] for c in conf_int]; hi = [c[1] for c in conf_int]
            ax.fill_between(fc_x, lo, hi, alpha=0.2, color="tomato", label="95% CI")
            ax.set_title(f"ARIMA Forecast — {source_key}"); ax.legend()
            plt.tight_layout()
            path = os.path.join(plot_dir, f"arima_{source_key}.png")
            plt.savefig(path, dpi=90); plt.close(fig); paths.append(path)
        except Exception:
            pass
        return paths

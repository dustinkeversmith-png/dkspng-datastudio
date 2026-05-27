"""Fourier signal-analysis model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class FourierModel(BaseModel):
    model_key = "fourier"
    task_type = "signal"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else (X.columns[0] if not X.empty else None)
        series = (y if y is not None else X.iloc[:, 0]).dropna()

        try:
            import numpy as np

            signal = series.values.astype(float)
            N = len(signal)
            if N < 4:
                raise ValueError("Signal too short for Fourier analysis")

            fft_vals = np.fft.rfft(signal)
            freqs = np.fft.rfftfreq(N)
            amplitudes = np.abs(fft_vals)
            phases = np.angle(fft_vals)
            spectral_energy = float(np.sum(amplitudes**2))

            top_n = min(5, len(freqs))
            top_idx = np.argsort(amplitudes)[::-1][:top_n]
            dominant_freqs = [round(float(freqs[i]), 6) for i in top_idx]
            dominant_amps = [round(float(amplitudes[i]), 4) for i in top_idx]

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metrics={
                    "dominant_frequencies": dominant_freqs,
                    "dominant_amplitudes": dominant_amps,
                    "spectral_energy": round(spectral_energy, 2),
                    "n_samples": N,
                },
                uncertainty={"frequency_domain_uncertainty": round(1.0/N, 6)},
                lineage={"n_fft_bins": len(freqs)},
            )
        except Exception as e:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=str(target),
                metadata={"warning": f"Fourier failed: {e}"},
            )

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

"""Fourier signal-analysis model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from app.models.base_model import BaseModel, register_model
from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation


@register_model
class FourierModel(BaseModel):
    model_key = "fourier"
    task_type = "signal"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else (X.columns[0] if not X.empty else None)
        chart_paths: list[str] = []
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

            if context.get("plot"):
                chart_paths = self._plot(freqs, amplitudes, signal, source_key, context["plot_dir"])

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
                chart_paths=chart_paths,
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

    @staticmethod
    def _plot(freqs, amplitudes, signal, source_key, plot_dir) -> list[str]:
        paths: list[str] = []
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt, os
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            axes[0].plot(range(len(signal)), signal, color="#5b8db8", lw=0.8)
            axes[0].set_title(f"Signal — {source_key}"); axes[0].set_xlabel("Sample")
            axes[1].plot(freqs[1:], amplitudes[1:], color="darkorange", lw=0.8)
            axes[1].set_title("Fourier Spectrum"); axes[1].set_xlabel("Frequency"); axes[1].set_ylabel("Amplitude")
            plt.tight_layout()
            path = os.path.join(plot_dir, f"fourier_{source_key}.png")
            plt.savefig(path, dpi=90); plt.close(fig); paths.append(path)
        except Exception:
            pass
        return paths

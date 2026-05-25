"""PCA dimensionality-reduction model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from app.models.base_model import BaseModel, register_model
from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation


@register_model
class PCAModel(BaseModel):
    model_key = "pca"
    task_type = "decomposition"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        n_components = context.get("n_components", min(3, len(X.columns)))
        chart_paths: list[str] = []
        try:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            import numpy as np, os
            Xs = StandardScaler().fit_transform(X)
            pca = PCA(n_components=n_components)
            comps = pca.fit_transform(Xs)
            evr = pca.explained_variance_ratio_.tolist()
            recon_err = float(np.mean((Xs - pca.inverse_transform(comps)) ** 2))
            if context.get("plot"):
                chart_paths = self._plot(comps, evr, source_key, context["plot_dir"])
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=None,
                metrics={"explained_variance_ratio": [round(v,4) for v in evr],
                         "total_variance_explained": round(sum(evr),4),
                         "reconstruction_error": round(recon_err,6)},
                uncertainty={"reconstruction_mse": round(recon_err,6)},
                lineage={"n_components": n_components,
                         "loadings": [[round(v,4) for v in r] for r in pca.components_.tolist()]},
                chart_paths=chart_paths, fitted_model_ref=pca,
            )
        except ImportError:
            return ModelResult(model_key=self.model_key, task_type=self.task_type,
                               source_key=source_key, feature_fields=list(X.columns),
                               target_field=None, metadata={"warning": "sklearn not available"})

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

    @staticmethod
    def _plot(comps, evr, source_key, plot_dir) -> list[str]:
        paths: list[str] = []
        try:
            import matplotlib; matplotlib.use("Agg")
            import matplotlib.pyplot as plt, os
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
            y2 = comps[:, 1] if comps.shape[1] > 1 else [0]*len(comps)
            axes[0].scatter(comps[:, 0], y2, alpha=0.5, s=15, c=range(len(comps)), cmap="viridis")
            axes[0].set_xlabel("PC1"); axes[0].set_ylabel("PC2")
            axes[0].set_title(f"PCA Biplot — {source_key}")
            axes[1].bar(range(1, len(evr)+1), evr, color="#5b8db8")
            axes[1].set_xlabel("Component"); axes[1].set_ylabel("Variance Explained")
            axes[1].set_title("Explained Variance")
            plt.tight_layout()
            path = os.path.join(plot_dir, f"pca_{source_key}.png")
            plt.savefig(path, dpi=90); plt.close(fig); paths.append(path)
        except Exception:
            pass
        return paths

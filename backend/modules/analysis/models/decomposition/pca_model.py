"""PCA dimensionality-reduction model."""
from __future__ import annotations
from typing import Any
import pandas as pd
from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class PCAModel(BaseModel):
    model_key = "pca"
    task_type = "decomposition"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        n_components = context.get("n_components", min(3, len(X.columns)))
        try:
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            import numpy as np
            Xs = StandardScaler().fit_transform(X)
            pca = PCA(n_components=n_components)
            comps = pca.fit_transform(Xs)
            evr = pca.explained_variance_ratio_.tolist()
            recon_err = float(np.mean((Xs - pca.inverse_transform(comps)) ** 2))
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns), target_field=None,
                metrics={"explained_variance_ratio": [round(v,4) for v in evr],
                         "total_variance_explained": round(sum(evr),4),
                         "reconstruction_error": round(recon_err,6)},
                uncertainty={"reconstruction_mse": round(recon_err,6)},
                lineage={"n_components": n_components,
                         "loadings": [[round(v,4) for v in r] for r in pca.components_.tolist()]},
                fitted_model_ref=pca,
            )
        except ImportError:
            return ModelResult(model_key=self.model_key, task_type=self.task_type,
                               source_key=source_key, feature_fields=list(X.columns),
                               target_field=None, metadata={"warning": "sklearn not available"})

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

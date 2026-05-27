"""SVM classifier model."""
from __future__ import annotations
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class SVMModel(BaseModel):
    model_key = "svm"
    task_type = "classification"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None

        try:
            from sklearn.svm import SVC
            from sklearn.preprocessing import LabelEncoder, StandardScaler
            from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

            le = LabelEncoder()
            y_enc = le.fit_transform(y.astype(str))
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = SVC(kernel="rbf", probability=True, random_state=42)
            model.fit(X_scaled, y_enc)
            preds = model.predict(X_scaled)

            acc = float(accuracy_score(y_enc, preds))
            f1 = float(f1_score(y_enc, preds, average="weighted", zero_division=0))
            cm = confusion_matrix(y_enc, preds).tolist()

            proba = model.predict_proba(X_scaled)
            import numpy as np
            entropy = float(np.mean(-np.sum(proba * np.log(proba + 1e-9), axis=1)))

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target,
                metrics={"accuracy": round(acc, 4), "f1": round(f1, 4), "confusion_matrix": cm},
                uncertainty={"class_entropy": round(entropy, 4)},
                predictions=le.inverse_transform(preds).tolist(),
                fitted_model_ref=model,
            )
        except ImportError:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target, metadata={"warning": "sklearn not available"},
            )

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)



"""Naive Bayes classifier model."""
from __future__ import annotations
from typing import Any

import pandas as pd

from app.models.base_model import BaseModel, register_model
from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation


@register_model
class NaiveBayesModel(BaseModel):
    model_key = "naive_bayes"
    task_type = "classification"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None

        try:
            from sklearn.naive_bayes import GaussianNB
            from sklearn.preprocessing import LabelEncoder
            from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
            import numpy as np

            le = LabelEncoder()
            y_enc = le.fit_transform(y.astype(str))
            model = GaussianNB()
            model.fit(X, y_enc)
            preds = model.predict(X)

            acc = float(accuracy_score(y_enc, preds))
            f1 = float(f1_score(y_enc, preds, average="weighted", zero_division=0))
            cm = confusion_matrix(y_enc, preds).tolist()
            proba = model.predict_proba(X)
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

"""Logistic regression model."""
from __future__ import annotations
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class LogisticRegressionModel(BaseModel):
    model_key = "logistic_regression"
    task_type = "classification"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None

        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, confusion_matrix,
            )
            import numpy as np

            le = LabelEncoder()
            y_enc = le.fit_transform(y.astype(str))

            model = LogisticRegression(max_iter=500, multi_class="auto")
            model.fit(X, y_enc)
            preds = model.predict(X)

            acc = float(accuracy_score(y_enc, preds))
            prec = float(precision_score(y_enc, preds, average="weighted", zero_division=0))
            rec = float(recall_score(y_enc, preds, average="weighted", zero_division=0))
            f1 = float(f1_score(y_enc, preds, average="weighted", zero_division=0))
            cm = confusion_matrix(y_enc, preds).tolist()

            metrics = {"accuracy": round(acc, 4), "precision": round(prec, 4),
                       "recall": round(rec, 4), "f1": round(f1, 4),
                       "confusion_matrix": cm}

            proba = model.predict_proba(X)
            entropy = float(np.mean(-np.sum(proba * np.log(proba + 1e-9), axis=1)))
            uncertainty = {"class_entropy": round(entropy, 4)}

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target, metrics=metrics, uncertainty=uncertainty,
                predictions=le.inverse_transform(preds).tolist(),
                fitted_model_ref=model,
                lineage={"classes": le.classes_.tolist()},
            )
        except ImportError:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target, metadata={"warning": "sklearn not available"},
            )

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

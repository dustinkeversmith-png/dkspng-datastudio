"""Decision tree model."""
from __future__ import annotations
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@register_model
class DecisionTreeModel(BaseModel):
    model_key = "decision_tree"
    task_type = "classification"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = y.name if y is not None else None

        try:
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.preprocessing import LabelEncoder
            from sklearn.metrics import accuracy_score, f1_score
            import numpy as np

            le = LabelEncoder()
            y_enc = le.fit_transform(y.astype(str))
            model = DecisionTreeClassifier(max_depth=6, random_state=42)
            model.fit(X, y_enc)
            preds = model.predict(X)
            proba = model.predict_proba(X)

            acc = float(accuracy_score(y_enc, preds))
            f1 = float(f1_score(y_enc, preds, average="weighted", zero_division=0))
            entropy = float(np.mean(-np.sum(proba * np.log(proba + 1e-9), axis=1)))
            importances = dict(zip(X.columns.tolist(), model.feature_importances_.tolist()))

            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target,
                metrics={"accuracy": round(acc, 4), "f1": round(f1, 4),
                         "feature_importances": {k: round(v, 4) for k, v in importances.items()}},
                uncertainty={"class_entropy": round(entropy, 4)},
                predictions=le.inverse_transform(preds).tolist(),
                fitted_model_ref=model,
                lineage={"max_depth": 6, "n_classes": len(le.classes_)},
            )
        except ImportError:
            return ModelResult(
                model_key=self.model_key, task_type=self.task_type,
                source_key=source_key, feature_fields=list(X.columns),
                target_field=target, metadata={"warning": "sklearn not available"},
            )

    def predict(self, X, context): return PredictionResult(model_key=self.model_key)
    def evaluate(self, X, y, context): return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)



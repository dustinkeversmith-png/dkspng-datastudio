"""ModelEngine — runs a model on a DataFrame, emits ModelResult + chart."""
from __future__ import annotations

import os
from typing import Any

import pandas as pd

from app.models.model_result import ModelResult


_PLOT_DIR = os.path.join("data", "plots", "project2")


class ModelEngine:
    """Orchestrates fit → evaluate → chart for a single model × DataFrame pair."""

    def __init__(self, df: pd.DataFrame, source_key: str) -> None:
        self.df = df.copy()
        self.source_key = source_key

    def run(
        self,
        model_key: str,
        features: list[str],
        target: str | None = None,
        plot: bool = True,
        extra_context: dict[str, Any] | None = None,
    ) -> ModelResult:
        """Fit and evaluate *model_key* on the DataFrame.

        Parameters
        ----------
        model_key:  One of the registered model keys.
        features:   Feature column names.
        target:     Target column (None for unsupervised models).
        plot:       Whether to generate and save charts.
        extra_context: Passed through to model.fit/evaluate as context dict.
        """
        from app.models.base_model import get_model

        context: dict[str, Any] = {
            "source_key": self.source_key,
            "plot_dir": _PLOT_DIR,
            "plot": plot,
            **(extra_context or {}),
        }

        os.makedirs(_PLOT_DIR, exist_ok=True)

        # Prepare data
        all_cols = [c for c in features if c in self.df.columns]
        if target and target in self.df.columns:
            all_cols_with_target = all_cols + [target]
        else:
            all_cols_with_target = all_cols
            target = None

        sub = self.df[all_cols_with_target].copy()
        for col in all_cols_with_target:
            sub[col] = pd.to_numeric(sub[col], errors="coerce")
        sub = sub.dropna()

        if sub.empty:
            return ModelResult(
                model_key=model_key,
                task_type="unknown",
                source_key=self.source_key,
                feature_fields=features,
                target_field=target,
                metadata={"warning": "No valid rows after numeric coercion / dropna"},
            )

        X = sub[all_cols]
        y = sub[target] if target else None

        try:
            ModelCls = get_model(model_key)
            model = ModelCls()
            result = model.fit(X, y, context)
            return result
        except KeyError as e:
            return ModelResult(
                model_key=model_key,
                task_type="unknown",
                source_key=self.source_key,
                feature_fields=features,
                target_field=target,
                metadata={"error": str(e)},
            )
        except Exception as e:
            return ModelResult(
                model_key=model_key,
                task_type="unknown",
                source_key=self.source_key,
                feature_fields=features,
                target_field=target,
                metadata={"error": str(e)},
            )

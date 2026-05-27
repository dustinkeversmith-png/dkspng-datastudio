"""Base model ABC and model registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseModel(ABC):
    """Abstract base for all analysis models."""

    model_key: str = "base"
    task_type: str = "unknown"   # "regression" | "classification" | "clustering" | "time_series" | "signal" | "decomposition"

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> "ModelResult":
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame, context: dict[str, Any]) -> "PredictionResult":
        ...

    @abstractmethod
    def evaluate(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> "ModelEvaluation":
        ...

    def _safe_import(self, module: str, attribute: str | None = None):
        """Try importing a module; return None on ImportError."""
        try:
            import importlib
            mod = importlib.import_module(module)
            if attribute:
                return getattr(mod, attribute)
            return mod
        except ImportError:
            return None


# Lazy registry — populated by each model module at import time
_MODEL_REGISTRY: dict[str, type[BaseModel]] = {}


def register_model(cls: type[BaseModel]) -> type[BaseModel]:
    _MODEL_REGISTRY[cls.model_key] = cls
    return cls


def get_model(model_key: str) -> type[BaseModel]:
    if model_key not in _MODEL_REGISTRY:
        raise KeyError(f"Unknown model_key: {model_key!r}. Available: {list(_MODEL_REGISTRY)}")
    return _MODEL_REGISTRY[model_key]


def list_models() -> list[str]:
    return list(_MODEL_REGISTRY.keys())

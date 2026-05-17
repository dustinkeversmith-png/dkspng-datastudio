"""Typed result objects for analysis methods."""
from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class RegressionResult:
    """Result of Source.log_regression()."""
    weights: list[float]
    bias: float
    r2: float
    feature_cols: list[str]
    target_col: str
    points: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self) -> str:
        return (
            f"RegressionResult(r2={self.r2:.4f}, "
            f"weights={self.weights}, bias={self.bias:.4f})"
        )


@dataclass
class KNNResult:
    """Result of Source.knn()."""
    n_neighbors: int
    model_type: str
    feature_cols: list[str]
    target_col: str
    points: pd.DataFrame = field(default_factory=pd.DataFrame)
    classes: list = field(default_factory=list)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self) -> str:
        return (
            f"KNNResult(n_neighbors={self.n_neighbors}, "
            f"model_type={self.model_type!r}, "
            f"classes={self.classes})"
        )

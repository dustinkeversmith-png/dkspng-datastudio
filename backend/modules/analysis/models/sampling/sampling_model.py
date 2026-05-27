"""Registered sampling diagnostics model."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@dataclass
class SamplingResult:
    """Typed result for uncertainty, bias, and confidence interval diagnostics."""

    source_key: str
    target: str | None
    method: str
    sample_size: int
    population_size: int | None = None
    statistic: str | None = None
    estimate: float | None = None
    uncertainty: float | None = None
    confidence_interval: tuple[float, float] | None = None
    bias_score: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model_result(self) -> ModelResult:
        return ModelResult(
            model_key=SamplingModel.model_key,
            task_type=SamplingModel.task_type,
            source_key=self.source_key,
            feature_fields=[self.target] if self.target else [],
            target_field=self.target,
            metrics={
                "sample_size": self.sample_size,
                "population_size": self.population_size,
                "statistic": self.statistic,
                "estimate": self.estimate,
                "bias_score": self.bias_score,
            },
            uncertainty={
                "standard_error": self.uncertainty,
                "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            },
            metadata={**self.metadata, "method": self.method, "warnings": self.warnings},
        )


@register_model
class SamplingModel(BaseModel):
    """Run per-source sampling diagnostics through the model registry."""

    model_key = "sampling_diagnostics"
    task_type = "sampling"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        target = context.get("target") or (y.name if y is not None else self._first_numeric_column(X))
        method = context.get("method", "uncertainty_if")

        if method == "bias_if":
            result = self.bias_if(
                df=X,
                source_key=source_key,
                condition=context.get("condition", {}),
                compare_to=context.get("compare_to", "full_source"),
                target=target,
            )
        elif method == "confidence_interval":
            result = self.confidence_interval(
                df=X,
                source_key=source_key,
                target=target,
                confidence=float(context.get("confidence", 0.95)),
                method=context.get("interval_method", "t_interval"),
            )
        else:
            result = self.uncertainty_if(
                df=X,
                source_key=source_key,
                target=target,
                sample_size=int(context.get("sample_size", 100)),
                confidence=float(context.get("confidence", 0.95)),
                method=context.get("sampling_method", "bootstrap"),
                n_bootstrap=int(context.get("n_bootstrap", 1000)),
            )
        return result.to_model_result()

    def predict(self, X: pd.DataFrame, context: dict[str, Any]) -> PredictionResult:
        return PredictionResult(model_key=self.model_key)

    def evaluate(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelEvaluation:
        return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

    def uncertainty_if(
        self,
        df: pd.DataFrame,
        source_key: str,
        target: str | None,
        sample_size: int = 100,
        confidence: float = 0.95,
        method: str = "bootstrap",
        n_bootstrap: int = 1000,
    ) -> SamplingResult:
        """Estimate mean uncertainty from a sample of the selected target column."""
        if not target or target not in df.columns:
            return SamplingResult(source_key=source_key, target=target, method=method, sample_size=0, warnings=["Target column not found"])

        series = pd.to_numeric(df[target], errors="coerce").dropna()
        pop_size = len(series)
        n = min(sample_size, pop_size)
        if n < 2:
            return SamplingResult(source_key=source_key, target=target, method=method, sample_size=n, population_size=pop_size, warnings=["Insufficient data for sampling"])

        sample = series.sample(n=n, random_state=42).values.tolist()
        if method == "bootstrap":
            ci, se = self._bootstrap_ci(sample, n_bootstrap, confidence)
        elif method == "t_interval":
            ci, se = self._t_interval(sample, confidence)
        else:
            ci, se = self._z_interval(sample, confidence)

        warnings: list[str] = []
        if pop_size < 30:
            warnings.append("Small population: results may not be reliable")
        if n < 30:
            warnings.append("Small sample: consider increasing sample_size")

        estimate = sum(sample) / len(sample)
        return SamplingResult(
            source_key=source_key,
            target=target,
            method=method,
            sample_size=n,
            population_size=pop_size,
            statistic="mean",
            estimate=round(estimate, 6),
            uncertainty=round(se, 6),
            confidence_interval=(round(ci[0], 6), round(ci[1], 6)),
            warnings=warnings,
            metadata={"confidence": confidence},
        )

    def bias_if(
        self,
        df: pd.DataFrame,
        source_key: str,
        condition: dict[str, Any],
        compare_to: str = "full_source",
        target: str | None = None,
    ) -> SamplingResult:
        """Compare a conditioned subgroup against the remaining rows."""
        field = condition.get("field", "")
        op = condition.get("op", "==")
        value = condition.get("value")
        if field not in df.columns:
            return SamplingResult(source_key=source_key, target=target, method="bias_if", sample_size=0, warnings=[f"Condition field '{field}' not found"])

        target = target or self._first_numeric_column(df)
        if target is None or target not in df.columns:
            return SamplingResult(source_key=source_key, target=target, method="bias_if", sample_size=0, population_size=len(df), warnings=["No numeric target column found for bias comparison"])

        mask = self._apply_op(df[field], op, value)
        group_vals = pd.to_numeric(df[mask][target], errors="coerce").dropna()
        rest_vals = pd.to_numeric(df[~mask][target], errors="coerce").dropna()
        warnings: list[str] = []
        if len(group_vals) < 2 or len(rest_vals) < 2:
            warnings.append("Too few rows in group or complement for bias analysis")
            return SamplingResult(source_key=source_key, target=target, method="bias_if", sample_size=len(group_vals), population_size=len(df), warnings=warnings)

        group_mean = float(group_vals.mean())
        rest_mean = float(rest_vals.mean())
        bias_score = (group_mean - rest_mean) / (rest_mean + 1e-9)
        if abs(bias_score) > 0.2:
            warnings.append(f"Substantial bias detected: group mean={group_mean:.3f} vs complement mean={rest_mean:.3f}")

        return SamplingResult(
            source_key=source_key,
            target=target,
            method="bias_if",
            sample_size=len(group_vals),
            population_size=len(df),
            statistic="mean_difference",
            estimate=round(group_mean - rest_mean, 6),
            bias_score=round(bias_score, 6),
            warnings=warnings,
            metadata={
                "condition": condition,
                "compare_to": compare_to,
                "group_mean": round(group_mean, 6),
                "complement_mean": round(rest_mean, 6),
                "group_n": len(group_vals),
                "complement_n": len(rest_vals),
            },
        )

    def confidence_interval(
        self,
        df: pd.DataFrame,
        source_key: str,
        target: str | None,
        confidence: float = 0.95,
        method: str = "t_interval",
    ) -> SamplingResult:
        """Compute a confidence interval for the mean of a target column."""
        if not target or target not in df.columns:
            return SamplingResult(source_key=source_key, target=target, method=method, sample_size=0, warnings=["Target column not found"])

        series = pd.to_numeric(df[target], errors="coerce").dropna()
        n = len(series)
        if n < 2:
            return SamplingResult(source_key=source_key, target=target, method=method, sample_size=n, warnings=["Insufficient data"])

        sample = series.values.tolist()
        if method == "bootstrap":
            ci, se = self._bootstrap_ci(sample, 1000, confidence)
        elif method == "z_interval":
            ci, se = self._z_interval(sample, confidence)
        else:
            ci, se = self._t_interval(sample, confidence)

        estimate = sum(sample) / len(sample)
        return SamplingResult(
            source_key=source_key,
            target=target,
            method=method,
            sample_size=n,
            population_size=n,
            statistic="mean",
            estimate=round(estimate, 6),
            uncertainty=round(se, 6),
            confidence_interval=(round(ci[0], 6), round(ci[1], 6)),
            metadata={"confidence": confidence},
        )

    @staticmethod
    def _first_numeric_column(df: pd.DataFrame) -> str | None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        return numeric_cols[0] if numeric_cols else None

    @staticmethod
    def _mean(values: list[float]) -> float:
        return sum(values) / len(values)

    @staticmethod
    def _std(values: list[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        m = sum(values) / n
        return math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))

    def _bootstrap_ci(self, sample: list[float], n_iter: int, confidence: float) -> tuple[tuple[float, float], float]:
        n = len(sample)
        boot_means: list[float] = []
        rng = random.Random(42)
        for _ in range(n_iter):
            boot_means.append(self._mean([rng.choice(sample) for _ in range(n)]))

        boot_means.sort()
        alpha = 1 - confidence
        lo_i = int(alpha / 2 * n_iter)
        hi_i = int((1 - alpha / 2) * n_iter)
        return (boot_means[lo_i], boot_means[min(hi_i, n_iter - 1)]), self._std(boot_means)

    def _t_interval(self, sample: list[float], confidence: float) -> tuple[tuple[float, float], float]:
        n = len(sample)
        m = self._mean(sample)
        se = self._std(sample) / math.sqrt(n)
        try:
            from scipy import stats as _stats
            t_crit = _stats.t.ppf((1 + confidence) / 2, df=n - 1)
        except ImportError:
            t_crit = self._approx_t_crit(n - 1, confidence)
        margin = t_crit * se
        return (m - margin, m + margin), se

    def _z_interval(self, sample: list[float], confidence: float) -> tuple[tuple[float, float], float]:
        n = len(sample)
        m = self._mean(sample)
        se = self._std(sample) / math.sqrt(n)
        z_table = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
        margin = z_table.get(round(confidence, 2), 1.960) * se
        return (m - margin, m + margin), se

    @staticmethod
    def _approx_t_crit(df: int, confidence: float) -> float:
        if df > 30:
            return {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}.get(round(confidence, 2), 1.960)
        small_df = {1: 12.706, 2: 4.303, 5: 2.571, 10: 2.228, 20: 2.086, 30: 2.042}
        key = min(small_df.keys(), key=lambda k: abs(k - df))
        return small_df[key]

    @staticmethod
    def _apply_op(col: pd.Series, op: str, value: Any) -> pd.Series:
        if op == "==":
            return col == value
        if op == "!=":
            return col != value
        if op == ">":
            return col > value
        if op == "<":
            return col < value
        if op == ">=":
            return col >= value
        if op == "<=":
            return col <= value
        return pd.Series([True] * len(col), index=col.index)

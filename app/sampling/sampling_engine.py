"""
SamplingEngine — per-source uncertainty, bias, and confidence-interval analysis.

Usage
-----
    engine = SamplingEngine(df, source_key="noaa_gsod")

    result = engine.uncertainty_if("TEMP", sample_size=100, confidence=0.95, method="bootstrap")
    result = engine.bias_if(condition={"field": "county", "op": "==", "value": "Klamath"},
                             compare_to="full_source")
    result = engine.confidence_interval("AQI", confidence=0.95, method="t_interval")
"""
from __future__ import annotations

import math
import random
from typing import Any

import pandas as pd

from app.sampling.results import SamplingResult


class SamplingEngine:
    """Attaches to a single DataFrame and provides sampling diagnostics."""

    def __init__(self, df: pd.DataFrame, source_key: str) -> None:
        self.df = df.copy()
        self.source_key = source_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def uncertainty_if(
        self,
        target: str,
        sample_size: int = 100,
        confidence: float = 0.95,
        method: str = "bootstrap",
        n_bootstrap: int = 1000,
    ) -> SamplingResult:
        """Estimate the uncertainty of a statistic computed on a sample.

        Parameters
        ----------
        target:       Column name to analyse.
        sample_size:  Rows to sample (capped at len(df)).
        confidence:   Confidence level, e.g. 0.95.
        method:       "bootstrap" | "t_interval" | "z_interval"
        n_bootstrap:  Iterations when method=="bootstrap".
        """
        warnings: list[str] = []

        if target not in self.df.columns:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method=method,
                sample_size=0,
                warnings=[f"Column '{target}' not found"],
            )

        series = pd.to_numeric(self.df[target], errors="coerce").dropna()
        pop_size = len(series)
        n = min(sample_size, pop_size)

        if n < 2:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method=method,
                sample_size=n,
                population_size=pop_size,
                warnings=["Insufficient data for sampling"],
            )

        sample = series.sample(n=n, random_state=42).values.tolist()

        if method == "bootstrap":
            ci, se = self._bootstrap_ci(sample, n_bootstrap, confidence)
        elif method == "t_interval":
            ci, se = self._t_interval(sample, confidence)
        else:
            ci, se = self._z_interval(sample, confidence)

        estimate = sum(sample) / len(sample)

        if pop_size < 30:
            warnings.append("Small population: results may not be reliable")
        if n < 30:
            warnings.append("Small sample: consider increasing sample_size")

        return SamplingResult(
            source_key=self.source_key,
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
        condition: dict[str, Any],
        compare_to: str = "full_source",
        target: str | None = None,
    ) -> SamplingResult:
        """Check whether a conditioned sub-group differs from the full source.

        Parameters
        ----------
        condition:  {"field": str, "op": str, "value": Any}
                    Supported ops: "==", "!=", ">", "<", ">=", "<="
        compare_to: "full_source" (only option currently)
        target:     Numeric column to compare means on.  If None, uses first
                    numeric column found.
        """
        warnings: list[str] = []

        field = condition.get("field", "")
        op = condition.get("op", "==")
        value = condition.get("value")

        if field not in self.df.columns:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method="bias_if",
                sample_size=0,
                warnings=[f"Condition field '{field}' not found"],
            )

        col = self.df[field]
        mask = self._apply_op(col, op, value)
        group_df = self.df[mask]
        rest_df = self.df[~mask]

        if target is None:
            numeric_cols = self.df.select_dtypes(include="number").columns.tolist()
            target = numeric_cols[0] if numeric_cols else None

        if target is None or target not in self.df.columns:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method="bias_if",
                sample_size=len(group_df),
                population_size=len(self.df),
                warnings=["No numeric target column found for bias comparison"],
            )

        group_vals = pd.to_numeric(group_df[target], errors="coerce").dropna()
        rest_vals = pd.to_numeric(rest_df[target], errors="coerce").dropna()

        if len(group_vals) < 2 or len(rest_vals) < 2:
            warnings.append("Too few rows in group or complement for bias analysis")
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method="bias_if",
                sample_size=len(group_vals),
                population_size=len(self.df),
                warnings=warnings,
            )

        group_mean = float(group_vals.mean())
        rest_mean = float(rest_vals.mean())
        bias_score = (group_mean - rest_mean) / (rest_mean + 1e-9)

        if abs(bias_score) > 0.2:
            warnings.append(
                f"Substantial bias detected: group mean={group_mean:.3f} "
                f"vs complement mean={rest_mean:.3f} (bias={bias_score:.3f})"
            )

        return SamplingResult(
            source_key=self.source_key,
            target=target,
            method="bias_if",
            sample_size=len(group_vals),
            population_size=len(self.df),
            statistic="mean_difference",
            estimate=round(group_mean - rest_mean, 6),
            bias_score=round(bias_score, 6),
            warnings=warnings,
            metadata={
                "condition": condition,
                "group_mean": round(group_mean, 6),
                "complement_mean": round(rest_mean, 6),
                "group_n": len(group_vals),
                "complement_n": len(rest_vals),
            },
        )

    def confidence_interval(
        self,
        target: str,
        confidence: float = 0.95,
        method: str = "t_interval",
    ) -> SamplingResult:
        """Compute a confidence interval for the mean of *target*."""
        warnings: list[str] = []

        if target not in self.df.columns:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method=method,
                sample_size=0,
                warnings=[f"Column '{target}' not found"],
            )

        series = pd.to_numeric(self.df[target], errors="coerce").dropna()
        n = len(series)

        if n < 2:
            return SamplingResult(
                source_key=self.source_key,
                target=target,
                method=method,
                sample_size=n,
                warnings=["Insufficient data"],
            )

        sample = series.values.tolist()

        if method == "bootstrap":
            ci, se = self._bootstrap_ci(sample, 1000, confidence)
        elif method == "z_interval":
            ci, se = self._z_interval(sample, confidence)
        else:
            ci, se = self._t_interval(sample, confidence)

        estimate = sum(sample) / len(sample)

        return SamplingResult(
            source_key=self.source_key,
            target=target,
            method=method,
            sample_size=n,
            population_size=n,
            statistic="mean",
            estimate=round(estimate, 6),
            uncertainty=round(se, 6),
            confidence_interval=(round(ci[0], 6), round(ci[1], 6)),
            warnings=warnings,
            metadata={"confidence": confidence},
        )

    # ------------------------------------------------------------------
    # Internal statistics helpers (no scipy dependency)
    # ------------------------------------------------------------------

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

    def _bootstrap_ci(
        self,
        sample: list[float],
        n_iter: int,
        confidence: float,
    ) -> tuple[tuple[float, float], float]:
        n = len(sample)
        boot_means: list[float] = []
        rng = random.Random(42)
        for _ in range(n_iter):
            resample = [rng.choice(sample) for _ in range(n)]
            boot_means.append(self._mean(resample))

        boot_means.sort()
        alpha = 1 - confidence
        lo_i = int(alpha / 2 * n_iter)
        hi_i = int((1 - alpha / 2) * n_iter)
        ci = (boot_means[lo_i], boot_means[min(hi_i, n_iter - 1)])
        se = self._std(boot_means)
        return ci, se

    def _t_interval(
        self,
        sample: list[float],
        confidence: float,
    ) -> tuple[tuple[float, float], float]:
        """t-distribution CI using Welch's approximation via scipy if available."""
        n = len(sample)
        m = self._mean(sample)
        s = self._std(sample)
        se = s / math.sqrt(n)

        try:
            from scipy import stats as _stats
            t_crit = _stats.t.ppf((1 + confidence) / 2, df=n - 1)
        except ImportError:
            # Approximate t critical value for large n
            t_crit = self._approx_t_crit(n - 1, confidence)

        margin = t_crit * se
        return (m - margin, m + margin), se

    def _z_interval(
        self,
        sample: list[float],
        confidence: float,
    ) -> tuple[tuple[float, float], float]:
        n = len(sample)
        m = self._mean(sample)
        s = self._std(sample)
        se = s / math.sqrt(n)

        # z critical values for common confidence levels
        z_table = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
        z_crit = z_table.get(round(confidence, 2), 1.960)

        margin = z_crit * se
        return (m - margin, m + margin), se

    @staticmethod
    def _approx_t_crit(df: int, confidence: float) -> float:
        """Approximation of t-critical value using normal distribution for df > 30."""
        if df > 30:
            z_table = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
            return z_table.get(round(confidence, 2), 1.960)
        # For small df use conservative 95% values
        small_df = {1: 12.706, 2: 4.303, 5: 2.571, 10: 2.228, 20: 2.086, 30: 2.042}
        key = min(small_df.keys(), key=lambda k: abs(k - df))
        return small_df[key]

    @staticmethod
    def _apply_op(col: pd.Series, op: str, value: Any) -> pd.Series:
        if op == "==":
            return col == value
        elif op == "!=":
            return col != value
        elif op == ">":
            return col > value
        elif op == "<":
            return col < value
        elif op == ">=":
            return col >= value
        elif op == "<=":
            return col <= value
        return pd.Series([True] * len(col), index=col.index)

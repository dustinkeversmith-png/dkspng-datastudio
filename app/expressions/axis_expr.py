"""AxisExpr — deferred column expression for use in chart DSL.

Allows constructs like:
    s["fire"]["burn_rate"]                 → AxisExpr
    s["fire"]["burn_rate"].mean()          → AxisExpr (aggregated)
    s["fire"]["burn_rate"].where(cond)     → AxisExpr (filtered)
    s["fire"]["burn_rate"] * 2             → AxisExpr (arithmetic)
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable
import pandas as pd

if TYPE_CHECKING:
    from app.workflow.source_binding import Source


class AxisExpr:
    """A lazy column reference that resolves to a pd.Series when .resolve() is called."""

    def __init__(self, source: "Source", source_key: str, col_name: str):
        self._source = source
        self._source_key = source_key
        self._col_name = col_name
        self._transforms: list[Callable[[pd.Series], pd.Series]] = []
        self._filter: "AxisExpr | None" = None
        self._agg: str | None = None  # "mean", "stdev", "sum", "min", "max"

    # ------------------------------------------------------------------
    # Fluent API
    # ------------------------------------------------------------------

    def where(self, condition: "AxisExpr | pd.Series") -> "AxisExpr":
        """Apply a row-level boolean filter."""
        clone = self._clone()
        clone._filter = condition
        return clone

    def mean(self) -> "AxisExpr":
        return self._with_agg("mean")

    def stdev(self) -> "AxisExpr":
        return self._with_agg("stdev")

    def sum(self) -> "AxisExpr":
        return self._with_agg("sum")

    def min(self) -> "AxisExpr":
        return self._with_agg("min")

    def max(self) -> "AxisExpr":
        return self._with_agg("max")

    # ------------------------------------------------------------------
    # Arithmetic operators — return new AxisExpr wrapping a lambda
    # ------------------------------------------------------------------

    def __mul__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s * _coerce(other))

    def __truediv__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s / _coerce(other))

    def __add__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s + _coerce(other))

    def __sub__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s - _coerce(other))

    # Comparison — returns a boolean AxisExpr used as filter
    def __lt__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s < _coerce(other), boolean=True)

    def __le__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s <= _coerce(other), boolean=True)

    def __gt__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s > _coerce(other), boolean=True)

    def __ge__(self, other) -> "AxisExpr":
        return self._apply_op(lambda s: s >= _coerce(other), boolean=True)

    def __eq__(self, other) -> "AxisExpr":  # type: ignore[override]
        return self._apply_op(lambda s: s == _coerce(other), boolean=True)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self) -> pd.Series:
        """Evaluate the expression and return a concrete Series."""
        df = self._source.dataframes.get(self._source_key)
        if df is None:
            raise KeyError(f"Source '{self._source_key}' not found.")
        series = df[self._col_name].copy()

        # Apply all chained transforms
        for fn in self._transforms:
            series = fn(series)

        # Apply filter
        if self._filter is not None:
            mask = self._filter.resolve() if isinstance(self._filter, AxisExpr) else self._filter
            series = series[mask.values[:len(series)]]

        # Apply aggregation (broadcasts scalar back to a constant series)
        if self._agg:
            agg_map = {
                "mean": pd.Series.mean,
                "stdev": pd.Series.std,
                "sum": pd.Series.sum,
                "min": pd.Series.min,
                "max": pd.Series.max,
            }
            scalar = agg_map[self._agg](series)
            series = pd.Series([scalar] * len(series), index=series.index)

        return series

    @property
    def label(self) -> str:
        agg = f".{self._agg}()" if self._agg else ""
        return f"{self._source_key}[{self._col_name}]{agg}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _clone(self) -> "AxisExpr":
        new = AxisExpr(self._source, self._source_key, self._col_name)
        new._transforms = list(self._transforms)
        new._filter = self._filter
        new._agg = self._agg
        return new

    def _with_agg(self, agg: str) -> "AxisExpr":
        clone = self._clone()
        clone._agg = agg
        return clone

    def _apply_op(self, fn: Callable, boolean: bool = False) -> "AxisExpr":
        clone = self._clone()
        clone._transforms.append(fn)
        return clone

    def __repr__(self) -> str:
        return f"AxisExpr({self.label})"


def _coerce(other):
    """If other is an AxisExpr, resolve it; otherwise return as-is."""
    if isinstance(other, AxisExpr):
        return other.resolve()
    return other


class SourceProxy:
    """Returned by Source.__getitem__(source_key), allows s['fire']['col'] syntax."""

    def __init__(self, source: "Source", source_key: str):
        self._source = source
        self._source_key = source_key

    def __getitem__(self, col_name: str) -> AxisExpr:
        return AxisExpr(self._source, self._source_key, col_name)

    def __repr__(self) -> str:
        return f"SourceProxy(key={self._source_key!r})"

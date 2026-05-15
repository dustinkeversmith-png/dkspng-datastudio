"""
Map logical ``between(column, low, high)`` intents onto observation-store query keys.

Only dimensions backed by SQL filters are applied here; unknown columns are stored
under ``range_hints`` for future pipeline/parser stages.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _parse_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    s = str(val).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


class RangeQueryResolver:
    """Produces profile patches compatible with :func:`app.session_query_filters.effective_observation_filters`."""

    KNOWN_SQL_COLUMNS = frozenset(
        {"year", "observed_at", "metric_value", "metric_name"}
    )

    def between(self, column: str, low: Any, high: Any) -> dict[str, Any]:
        col = column.strip().lower()
        if col in ("year",):
            return {"year_min": int(low), "year_max": int(high)}
        if col in ("observed_at", "observed", "date", "time"):
            a = _parse_datetime(low)
            b = _parse_datetime(high)
            if not a or not b:
                raise ValueError("observed_at range requires parseable datetimes")
            return {"observed_at_min": a.isoformat(), "observed_at_max": b.isoformat()}
        if col in ("metric_value", "value"):
            return {"metric_value_min": float(low), "metric_value_max": float(high)}
        return {"range_hints": [{"column": column, "min": low, "max": high}]}

    def year_span(self, year_min: int, year_max: int) -> dict[str, Any]:
        return {"year_min": year_min, "year_max": year_max}

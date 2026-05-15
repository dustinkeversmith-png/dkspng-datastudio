"""Merge VisualizationSession query profiles with explicit observation-query kwargs."""

from __future__ import annotations

from typing import Any


def _pick(d: dict[str, Any], key: str, explicit: Any) -> Any:
    return explicit if explicit is not None else d.get(key)


def effective_observation_filters(
    *,
    session_profile: dict[str, Any],
    source_profile: dict[str, Any],
    category: str | None = None,
    county: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    bbox: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    search: str | None = None,
    observed_at_min: Any | None = None,
    observed_at_max: Any | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: list[str] | None = None,
) -> dict[str, Any]:
    """Later arguments override merged profiles when not ``None``."""
    base = {**session_profile, **source_profile}
    return {
        "category": _pick(base, "category", category),
        "county": _pick(base, "county", county),
        "city": _pick(base, "city", city),
        "state": _pick(base, "state", state),
        "year_min": _pick(base, "year_min", year_min),
        "year_max": _pick(base, "year_max", year_max),
        "bbox": _pick(base, "bbox", bbox),
        "latitude": _pick(base, "latitude", latitude),
        "longitude": _pick(base, "longitude", longitude),
        "radius_km": _pick(base, "radius_km", radius_km),
        "search": _pick(base, "search", search),
        "observed_at_min": _pick(base, "observed_at_min", observed_at_min),
        "observed_at_max": _pick(base, "observed_at_max", observed_at_max),
        "metric_value_min": _pick(base, "metric_value_min", metric_value_min),
        "metric_value_max": _pick(base, "metric_value_max", metric_value_max),
        "metric_names": _pick(base, "metric_names", metric_names),
    }

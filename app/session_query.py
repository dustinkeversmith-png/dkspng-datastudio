"""Resolve observation rows from either a legacy ``source_key`` filter or a VisualizationSession."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data_manipulation import apply_pipeline
from app.querying import query_observations
from app.session_query_filters import effective_observation_filters
from app.visualization_session import get_session


def verify_session_dataset(
    db: Session,
    session_id: str,
    dataset_id: str,
    *,
    sample_limit: int = 8000,
    preview_rows: int = 8,
    apply_session_filters: bool = True,
) -> dict:
    """Load up to ``sample_limit`` rows for one binding and return columns plus samples."""
    session = get_session(session_id)
    binding = session.datasets.get(dataset_id)
    if binding is None:
        raise KeyError(f"Dataset '{dataset_id}' is not part of session {session_id}")

    filt: dict = {}
    if apply_session_filters:
        filt = effective_observation_filters(
            session_profile=session.query_profile,
            source_profile=session.source_query_profiles.get(binding.source_key, {}),
        )

    rows = query_observations(db=db, source_key=binding.source_key, limit=sample_limit, **filt)
    columns: list[str] = []
    if rows:
        keys = set()
        for row in rows[:200]:
            keys.update(row.keys())
        columns = sorted(keys)

    sample = [dict(r) for r in rows[:preview_rows]]

    return {
        "dataset_id": dataset_id,
        "source_key": binding.source_key,
        "row_count": len(rows),
        "columns": columns,
        "sample_rows": sample,
        "truncated": len(rows) >= sample_limit,
    }


def fetch_session_observations(
    db: Session,
    session_id: str,
    *,
    category: str | None = None,
    county: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    bbox: str | None = None,
    limit: int = 1000,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    search: str | None = None,
    observed_at_min: object | None = None,
    observed_at_max: object | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: list[str] | None = None,
    extra_steps: list[dict] | None = None,
) -> list[dict]:
    session = get_session(session_id)
    if not session.datasets:
        return []

    n = len(session.datasets)
    per_cap = max(1, limit // n)

    merged: list[dict] = []
    for dataset_id, binding in session.datasets.items():
        filt = effective_observation_filters(
            session_profile=session.query_profile,
            source_profile=session.source_query_profiles.get(binding.source_key, {}),
            category=category,
            county=county,
            city=city,
            state=state,
            year_min=year_min,
            year_max=year_max,
            bbox=bbox,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            search=search,
            observed_at_min=observed_at_min,
            observed_at_max=observed_at_max,
            metric_value_min=metric_value_min,
            metric_value_max=metric_value_max,
            metric_names=metric_names,
        )
        part = query_observations(
            db=db,
            source_key=binding.source_key,
            limit=per_cap,
            **filt,
        )
        for row in part:
            row = dict(row)
            row["session_dataset_id"] = dataset_id
            row["session_source_key"] = binding.source_key
            merged.append(row)

    steps = list(session.pipeline)
    if extra_steps:
        steps.extend(extra_steps)
    merged = apply_pipeline(merged, steps)
    return merged[:limit]


def resolve_observation_rows(
    db: Session,
    *,
    session_id: str | None = None,
    source_key: str | None = None,
    category: str | None = None,
    county: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    bbox: str | None = None,
    limit: int = 1000,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    search: str | None = None,
    observed_at_min: object | None = None,
    observed_at_max: object | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: list[str] | None = None,
) -> list[dict]:
    if session_id:
        return fetch_session_observations(
            db,
            session_id,
            category=category,
            county=county,
            city=city,
            state=state,
            year_min=year_min,
            year_max=year_max,
            bbox=bbox,
            limit=limit,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            search=search,
            observed_at_min=observed_at_min,
            observed_at_max=observed_at_max,
            metric_value_min=metric_value_min,
            metric_value_max=metric_value_max,
            metric_names=metric_names,
        )

    return query_observations(
        db=db,
        source_key=source_key,
        category=category,
        county=county,
        city=city,
        state=state,
        year_min=year_min,
        year_max=year_max,
        bbox=bbox,
        limit=limit,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        search=search,
        observed_at_min=observed_at_min,
        observed_at_max=observed_at_max,
        metric_value_min=metric_value_min,
        metric_value_max=metric_value_max,
        metric_names=metric_names,
    )

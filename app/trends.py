from collections import defaultdict
from sqlalchemy.orm import Session
from app.session_query import resolve_observation_rows


def dataset_trends(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
):
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=10000,
    )

    grouped = defaultdict(list)

    for row in rows:
        if row.get("year") is None:
            continue

        value = row.get("metric_value")
        if value is None:
            value = 1

        series_key = row.get("session_dataset_id") or row["source_key"]
        grouped[(series_key, row["year"])].append(float(value))

    output = []

    for (series_key, year), values in grouped.items():
        output.append({
            "source_key": series_key,
            "year": year,
            "count": len(values),
            "sum": sum(values),
            "mean": sum(values) / len(values),
        })

    return sorted(output, key=lambda x: (x["source_key"], x["year"]))
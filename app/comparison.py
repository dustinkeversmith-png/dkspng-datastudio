from collections import defaultdict
from statistics import mean

from sqlalchemy.orm import Session

from app.querying import query_observations
from app.session_query import resolve_observation_rows


def _safe_label(value, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback
def compare_datasets(
    db: Session,
    source_keys: list[str] | None = None,
    session_id: str | None = None,
    county: str | None = None,
    city: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    limit: int = 50000,
) -> dict:
    grouped = defaultdict(list)

    if session_id:
        rows = resolve_observation_rows(
            db=db,
            session_id=session_id,
            county=county,
            city=city,
            year_min=year_min,
            year_max=year_max,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
        )
        for row in rows:
            key = row.get("session_dataset_id") or row.get("source_key") or "unknown"
            grouped[str(key)].append(row)

        if len(grouped) < 2:
            return {
                "status": "failed",
                "error": "Visualization session must contain at least two datasets.",
            }
    else:
        if not source_keys or len(source_keys) < 2:
            return {
                "status": "failed",
                "error": "Choose at least two datasets to compare (or use a visualization session).",
            }

        for source_key in source_keys:
            rows = query_observations(
                db=db,
                source_key=source_key,
                county=county,
                city=city,
                year_min=year_min,
                year_max=year_max,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                limit=limit,
            )

            grouped[source_key].extend(rows)

    output = []

    for group_key, rows in grouped.items():
        years = []
        values = []

        for row in rows:
            if row.get("year") is not None:
                years.append(int(row["year"]))

            if row.get("metric_value") is not None:
                try:
                    values.append(float(row["metric_value"]))
                except Exception:
                    pass

        item = {
            "row_count": len(rows),
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
            "metric_sum": sum(values) if values else None,
            "metric_mean": mean(values) if values else None,
            "available_numeric_count": len(values),
        }

        if session_id:
            item["dataset_id"] = group_key
            item["source_key"] = rows[0].get("source_key") if rows else None
        else:
            item["source_key"] = group_key

        output.append(item)

    return {
        "status": "success",
        "mode": "dataset_compare",
        "session_id": session_id,
        "datasets": output,
    }

def build_sankey(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 10000,
) -> dict:
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        category=category,
        county=county,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
    )

    labels: list[str] = []
    label_index: dict[str, int] = {}
    flow_values: dict[tuple[int, int], float] = defaultdict(float)

    def node(label: str) -> int:
        if label not in label_index:
            label_index[label] = len(labels)
            labels.append(label)
        return label_index[label]

    for row in rows:
        sid = row.get("session_dataset_id")
        source_label = sid if sid is not None else _safe_label(row.get("source_key"), "unknown")
        source = f"Source: {source_label}"
        dataset_category = f"Category: {_safe_label(row.get('dataset_category'), 'uncategorized')}"
        county_label = f"County: {_safe_label(row.get('county'), 'unknown')}"
        metric = f"Metric: {_safe_label(row.get('metric_name'), 'observation_count')}"

        value = row.get("metric_value")
        if value is None:
            value = 1.0
        else:
            try:
                value = abs(float(value))
                if value == 0:
                    value = 1.0
            except Exception:
                value = 1.0

        chain = [source, dataset_category, county_label, metric]
        for left, right in zip(chain, chain[1:]):
            flow_values[(node(left), node(right))] += value

    sources = []
    targets = []
    values = []

    for (src, dst), value in flow_values.items():
        sources.append(src)
        targets.append(dst)
        values.append(value)

    return {
        "status": "success",
        "mode": "sankey",
        "row_count": len(rows),
        "labels": labels,
        "sources": sources,
        "targets": targets,
        "values": values,
    }


def cross_domain_compare(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 10000,
) -> dict:
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        category=category,
        county=county,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
    )

    by_category: dict[str, list[dict]] = defaultdict(list)
    by_county: dict[str, list[dict]] = defaultdict(list)
    by_source: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        by_category[_safe_label(row.get("dataset_category"), "uncategorized")].append(row)
        by_county[_safe_label(row.get("county"), "unknown")].append(row)
        src = row.get("session_dataset_id") or row.get("source_key")
        by_source[_safe_label(src, "unknown")].append(row)

    def summarize(grouped: dict[str, list[dict]]) -> list[dict]:
        summaries = []

        for key, group_rows in grouped.items():
            numeric_values = []
            years = []

            for row in group_rows:
                if row.get("metric_value") is not None:
                    try:
                        numeric_values.append(float(row["metric_value"]))
                    except Exception:
                        pass

                if row.get("year") is not None:
                    try:
                        years.append(int(row["year"]))
                    except Exception:
                        pass

            summaries.append({
                "key": key,
                "observation_count": len(group_rows),
                "metric_sum": sum(numeric_values) if numeric_values else None,
                "metric_mean": mean(numeric_values) if numeric_values else None,
                "year_min": min(years) if years else None,
                "year_max": max(years) if years else None,
            })

        return sorted(summaries, key=lambda item: item["observation_count"], reverse=True)

    return {
        "status": "success",
        "mode": "cross_domain_compare",
        "row_count": len(rows),
        "by_category": summarize(by_category),
        "by_county": summarize(by_county),
        "by_source": summarize(by_source),
    }


def comparison_presets() -> dict:
    return {
        "status": "success",
        "presets": [
            {
                "key": "source_category_county_metric",
                "name": "Source to Category to County to Metric",
                "description": "Useful for Sankey diagrams and data lineage.",
                "flow": ["source_key", "dataset_category", "county", "metric_name"],
            },
            {
                "key": "hazard_vs_region",
                "name": "Hazard or Event Type by Region",
                "description": "Compare natural disaster observations by county and year.",
                "filters": ["category", "county", "year_min", "year_max"],
            },
            {
                "key": "regional_metric_rollup",
                "name": "Regional Metric Rollup",
                "description": "Group rows by county, category, and source.",
                "outputs": ["observation_count", "metric_sum", "metric_mean"],
            },
            {
                "key": "cross_domain_overlay_ready",
                "name": "Cross-Domain Overlay Ready",
                "description": "Prepares common summaries for overlaying disasters, injuries, and job market data.",
                "requires": ["normalized schema", "shared geography", "shared time range"],
            },
        ],
    }

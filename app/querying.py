from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def query_observations(
    db: Session,
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
    observed_at_min: str | datetime | None = None,
    observed_at_max: str | datetime | None = None,
    metric_value_min: float | None = None,
    metric_value_max: float | None = None,
    metric_names: list[str] | None = None,
) -> list[dict]:
    clauses = ["1=1"]
    params: dict = {"limit": limit}

    if source_key:
        clauses.append("source_key = :source_key")
        params["source_key"] = source_key

    if category:
        clauses.append("dataset_category = :category")
        params["category"] = category

    if county:
        clauses.append("LOWER(county) = LOWER(:county)")
        params["county"] = county

    if city:
        clauses.append("LOWER(city) = LOWER(:city)")
        params["city"] = city

    if state:
        clauses.append("LOWER(TRIM(COALESCE(state, ''))) = LOWER(TRIM(:state))")
        params["state"] = state.strip()

    if year_min is not None:
        clauses.append("year >= :year_min")
        params["year_min"] = year_min

    if year_max is not None:
        clauses.append("year <= :year_max")
        params["year_max"] = year_max

    if bbox:
        parts = [float(p.strip()) for p in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must use minLon,minLat,maxLon,maxLat")

        min_lon, min_lat, max_lon, max_lat = parts
        clauses.append(
            "geometry IS NOT NULL AND "
            "ST_Intersects(geometry, ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326))"
        )
        params.update({
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
        })

    if latitude is not None and longitude is not None and radius_km is not None:
        clauses.append("""
            geometry IS NOT NULL
            AND ST_DWithin(
                geography(geometry),
                geography(ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)),
                :radius_meters
            )
        """)
        params["latitude"] = latitude
        params["longitude"] = longitude
        params["radius_meters"] = radius_km * 1000

    if search:
        clauses.append(
            "("
            "LOWER(COALESCE(county, '')) LIKE :search OR "
            "LOWER(COALESCE(city, '')) LIKE :search OR "
            "LOWER(COALESCE(metric_name, '')) LIKE :search OR "
            "LOWER(COALESCE(observation_type, '')) LIKE :search"
            ")"
        )
        params["search"] = f"%{search.strip().lower()}%"

    if observed_at_min is not None:
        clauses.append("observed_at >= CAST(:observed_at_min AS timestamptz)")
        params["observed_at_min"] = (
            observed_at_min.isoformat() if isinstance(observed_at_min, datetime) else str(observed_at_min)
        )

    if observed_at_max is not None:
        clauses.append("observed_at <= CAST(:observed_at_max AS timestamptz)")
        params["observed_at_max"] = (
            observed_at_max.isoformat() if isinstance(observed_at_max, datetime) else str(observed_at_max)
        )

    if metric_value_min is not None:
        clauses.append("metric_value >= :metric_value_min")
        params["metric_value_min"] = float(metric_value_min)

    if metric_value_max is not None:
        clauses.append("metric_value <= :metric_value_max")
        params["metric_value_max"] = float(metric_value_max)

    if metric_names:
        parts = [f":mn_{i}" for i in range(len(metric_names))]
        clauses.append("metric_name IN (" + ", ".join(parts) + ")")
        for i, m in enumerate(metric_names):
            params[f"mn_{i}"] = m

    where_clause = " AND ".join(clauses)

    sql = text(f"""
        SELECT
            id::text,
            source_key,
            source_name,
            source_url,
            dataset_category,
            observation_type,
            observed_at,
            year,
            state,
            county,
            city,
            zip_code,
            latitude,
            longitude,
            metric_name,
            metric_value,
            unit,
            confidence_level,
            raw_properties_json
        FROM regional_observations
        WHERE {where_clause}
        ORDER BY year NULLS LAST, county NULLS LAST, city NULLS LAST
        LIMIT :limit
    """)

    return [dict(row) for row in db.execute(sql, params).mappings().all()]


def list_regions(db: Session) -> dict:
    counties = db.execute(text("""
        SELECT DISTINCT county
        FROM regional_observations
        WHERE county IS NOT NULL
        ORDER BY county
    """)).scalars().all()

    cities = db.execute(text("""
        SELECT DISTINCT city
        FROM regional_observations
        WHERE city IS NOT NULL
        ORDER BY city
    """)).scalars().all()

    categories = db.execute(text("""
        SELECT DISTINCT dataset_category
        FROM regional_observations
        WHERE dataset_category IS NOT NULL
        ORDER BY dataset_category
    """)).scalars().all()

    return {
        "counties": counties,
        "cities": cities,
        "categories": categories,
    }

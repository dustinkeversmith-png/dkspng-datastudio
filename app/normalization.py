import pandas as pd
from app.schemas import SourceDefinition


def _first_existing(row: pd.Series, names: list[str]):
    lower_map = {str(k).lower(): k for k in row.index}
    for name in names:
        key = lower_map.get(name.lower())
        if key is not None:
            value = row.get(key)
            if pd.notna(value):
                return value
    return None


def _as_float(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _as_int(value):
    try:
        if value is None or pd.isna(value):
            return None
        return int(float(value))
    except Exception:
        return None


def normalize_dataframe(source: SourceDefinition, df: pd.DataFrame) -> list[dict]:
    records: list[dict] = []
    lowered_columns = {str(c).lower() for c in df.columns}

    for _, row in df.iterrows():
        latitude = _as_float(_first_existing(row, source.latitude_fields))
        longitude = _as_float(_first_existing(row, source.longitude_fields))
        year = _as_int(_first_existing(row, source.year_fields))
        county = _first_existing(row, source.county_fields)

        metric_value = None
        metric_name = None

        for candidate in ["acres", "area", "count", "injuries", "jobs", "employment", "value"]:
            if candidate in lowered_columns:
                metric_name = candidate
                metric_value = _as_float(_first_existing(row, [candidate]))
                break

        city = _first_existing(row, ["city", "place"])
        zip_code = _first_existing(row, ["zip", "zip_code", "zipcode"])

        records.append({
            "source_key": source.source_key,
            "source_name": source.display_name,
            "source_url": source.source_url,
            "dataset_category": source.category,
            "observation_type": source.category,
            "observed_at": None,
            "year": year,
            "state": "OR",
            "county": str(county) if county is not None else None,
            "city": str(city) if city is not None else None,
            "zip_code": str(zip_code) if zip_code is not None else None,
            "latitude": latitude,
            "longitude": longitude,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "unit": None,
            "confidence_level": None,
            "raw_properties_json": {str(k): None if pd.isna(v) else v for k, v in row.to_dict().items()},
        })

    return records

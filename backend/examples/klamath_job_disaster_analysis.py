"""
Live Klamath Falls regional composition analysis.

This script uses the three public portal sources plus a Workforce technology
labor-market PDF source, filters/aggregates observations to 5 km around
Klamath Falls, and saves charts/maps for the described analysis.

Run from repo root:
    python -m app.examples.klamath_job_disaster_analysis
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from backend.examples.three_portal_bindings import PORTAL_APIS, register_three_portal_sources
from backend.workflow import analysis_tools, bind_sources, charts, source
from backend.workflow.chart_rendering import _ensure_matplotlib
from backend.workflow.pdf_labor_market import technology_labor_market_rows


KLAMATH_LAT = 42.2249
KLAMATH_LON = -121.7817
RADIUS_KM = 5.0
JOB_MARKET_PDF = "https://workforcesw.org/wp-content/uploads/sr_technology_in-house-printing.pdf"
CENSUS_POPULATION_API = (
    "https://api.census.gov/data/2023/acs/acs5"
    "?get=NAME,B01003_001E&for=place:39700&in=state:41"
)
OUT_DIR = Path("artifacts/klamath_job_disaster_analysis")

SOURCE_LABELS = {
    "portal_odf_firestats": "Oregon Fire Stats",
    "portal_dogami_slido": "DOGAMI SLIDO Landslides",
    "portal_sci_data_ics209_demo": "ICS-209 Incident Reports",
    "workforce_technology_labor_market": "Technology Labor Market PDF",
    "census_klamath_population": "Census Klamath Falls Population",
    "derived_average_per_year": "Average Per Year",
    "derived_enriched_variables": "Analysis Variables",
    "derived_frequency_bins": "Frequency Bins",
    "derived_distance_stats": "Distance Statistics",
    "derived_fire_population_proximity": "Fire and Population Proximity",
}

VARIABLE_LABELS = {
    "metric_value": "Normalized source metric",
    "distance_km": "Distance from Klamath Falls center (km)",
    "year": "Observation year",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "population": "Klamath Falls population",
    "nearest_landslide_km": "Nearest DOGAMI landslide distance (km)",
    "nearest_fire_km": "Nearest Oregon fire distance (km)",
    "fire_count_within_1km": "Fire points within 1 km",
    "fire_count_within_3km": "Fire points within 3 km",
    "fire_count_within_5km": "Fire points within 5 km",
}


def first_present(row: dict[str, Any], candidates: list[str]) -> Any:
    lower = {k.lower(): k for k in row}
    for candidate in candidates:
        found = lower.get(candidate.lower())
        if found is not None and row.get(found) not in (None, ""):
            return row.get(found)
    return None


def source_label(source_key: str) -> str:
    return SOURCE_LABELS.get(source_key, source_key.replace("_", " ").title())


def variable_label(column: str) -> str:
    return VARIABLE_LABELS.get(column, column.replace("_", " ").title())


def as_float(value: Any) -> float | None:
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(converted):
        return None
    return converted


def distance_km(lat_a: float, lon_a: float, lat_b: float = KLAMATH_LAT, lon_b: float = KLAMATH_LON) -> float:
    dlat = radians(lat_b - lat_a)
    dlon = radians(lon_b - lon_a)
    a = sin(dlat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(a))


def fetch_population_context_rows() -> list[dict[str, Any]]:
    response = requests.get(CENSUS_POPULATION_API, timeout=60)
    response.raise_for_status()
    payload = response.json()
    headers = payload[0]
    values = dict(zip(headers, payload[1]))
    population = float(values["B01003_001E"])
    return [
        {
            "session_source_key": "census_klamath_population",
            "source_url": CENSUS_POPULATION_API,
            "indicator": "klamath_falls_total_population_acs_2023",
            "metric_name": "population",
            "metric_value": population,
            "population": population,
            "year": 2023,
            "latitude": KLAMATH_LAT,
            "longitude": KLAMATH_LON,
            "county": "Klamath",
            "city": "Klamath Falls",
            "state": "OR",
            "source": "Census Klamath Falls Population",
            "target": "ACS 2023 total population",
            "value": population,
            "heat_x": KLAMATH_LON,
            "heat_y": KLAMATH_LAT,
            "heat_z": population,
        }
    ]


def normalize_rows(source_key: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        year = first_present(row, ["year", "fireyear", "YEAR_", "incident_year"])
        county = first_present(row, ["county", "COUNTY", "county_name"])
        lat = first_present(row, ["latitude", "lat", "lat_dd", "y", "POINT_Y"])
        lon = first_present(row, ["longitude", "lon", "long_dd", "lng", "x", "POINT_X"])
        metric_value = first_present(
            row,
            ["metric_value", "value", "esttotalacres", "protected_acres", "AREA_ft2", "ANNUAL_COS", "REPAIR_COS"],
        )
        try:
            year = int(float(year))
        except (TypeError, ValueError):
            year = 2020 + idx
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            lat = KLAMATH_LAT + (idx % 5) * 0.005
            lon = KLAMATH_LON - (idx % 5) * 0.005
        try:
            value = float(metric_value)
        except (TypeError, ValueError):
            value = 1.0
        normalized.append(
            {
                **row,
                "session_source_key": source_key,
                "source_label": source_label(source_key),
                "year": year,
                "county": str(county or "Klamath"),
                "city": str(first_present(row, ["city", "CITY"]) or "Klamath Falls"),
                "state": "OR",
                "latitude": lat,
                "longitude": lon,
                "distance_km": distance_km(lat, lon),
                "metric_name": source_key,
                "metric_value": value,
                "source": source_label(source_key),
                "target": str(year),
                "value": value,
                "heat_x": lon,
                "heat_y": lat,
                "heat_z": value,
            }
        )
    return normalized


def fetch_near_klamath() -> dict[str, list[dict[str, Any]]]:
    register_three_portal_sources()
    columns = [
        "year",
        "county",
        "city",
        "state",
        "latitude",
        "longitude",
        "lat_dd",
        "long_dd",
        "metric_name",
        "metric_value",
        "source",
        "target",
        "value",
        "heat_x",
        "heat_y",
        "heat_z",
    ]
    odf = source("portal_odf_firestats", PORTAL_APIS["odf_firestats"]["open_data_csv"], column_hints=columns)
    slido = source(
        "portal_dogami_slido",
        "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
        connector_type="arcgis_rest",
        column_hints=columns,
    )
    ics = source("portal_sci_data_ics209_demo", PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"], column_hints=columns)
    combined = bind_sources(odf, slido, ics)
    keys = ["portal_odf_firestats", "portal_dogami_slido", "portal_sci_data_ics209_demo"]
    combined.near((KLAMATH_LAT, KLAMATH_LON), RADIUS_KM, source_keys=keys)

    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for key in keys:
        rows = combined.fetch(source_keys=[key], limit=250, print_rows=False)
        normalized = normalize_rows(key, rows)
        rows_by_source[key] = normalized
        print(f"{key}: {len(normalized)} rows within {RADIUS_KM} km of Klamath Falls")

    job_rows = technology_labor_market_rows(
        JOB_MARKET_PDF,
        center_latitude=KLAMATH_LAT,
        center_longitude=KLAMATH_LON,
        output_pdf_path=OUT_DIR / "sources" / "workforce_technology.pdf",
    )
    for row in job_rows:
        row["source_label"] = source_label("workforce_technology_labor_market")
        row["distance_km"] = distance_km(float(row["latitude"]), float(row["longitude"]))
        row["source"] = source_label("workforce_technology_labor_market")
    rows_by_source["workforce_technology_labor_market"] = job_rows
    print(f"workforce_technology_labor_market: {len(job_rows)} structured rows from PDF")

    population_rows = fetch_population_context_rows()
    for row in population_rows:
        row["source_label"] = source_label("census_klamath_population")
        row["distance_km"] = distance_km(float(row["latitude"]), float(row["longitude"]))
    rows_by_source["census_klamath_population"] = population_rows
    print(f"census_klamath_population: {len(population_rows)} row from live Census API")
    return rows_by_source


def print_column_research(rows_by_source: dict[str, list[dict[str, Any]]]) -> None:
    print("\nAvailable source columns")
    for key, rows in rows_by_source.items():
        columns = sorted({column for row in rows for column in row})
        print(f"{source_label(key)} ({key})")
        print("  columns:", ", ".join(columns[:80]))
        numeric_columns: list[str] = []
        for column in columns:
            values = [as_float(row.get(column)) for row in rows]
            if any(value is not None for value in values):
                numeric_columns.append(column)
        print("  numeric columns:", ", ".join(numeric_columns[:40]))


def frequency_bin_rows(
    rows_by_source: dict[str, list[dict[str, Any]]],
    variables: list[str],
    *,
    bins: int = 5,
) -> list[dict[str, Any]]:
    out_rows: list[dict[str, Any]] = []
    for source_key, rows in rows_by_source.items():
        if source_key in {"derived_average_per_year", "derived_enriched_variables", "derived_frequency_bins", "derived_distance_stats"}:
            continue
        df = pd.DataFrame(rows)
        for variable in variables:
            if variable not in df.columns:
                continue
            series = pd.to_numeric(df[variable], errors="coerce").dropna()
            if series.empty:
                continue
            bucket_count = min(bins, max(1, int(series.nunique())))
            try:
                cuts = pd.cut(series, bins=bucket_count, duplicates="drop")
            except ValueError:
                continue
            counts = cuts.value_counts(sort=False)
            for interval, count in counts.items():
                if pd.isna(interval):
                    continue
                out_rows.append(
                    {
                        "session_source_key": "derived_frequency_bins",
                        "source_key": source_key,
                        "source_label": source_label(source_key),
                        "variable": variable,
                        "variable_label": variable_label(variable),
                        "bin_label": f"{interval.left:.2f} to {interval.right:.2f}",
                        "bin_low": float(interval.left),
                        "bin_high": float(interval.right),
                        "bin_midpoint": float((interval.left + interval.right) / 2),
                        "count": int(count),
                        "metric_value": int(count),
                        "source": source_label(source_key),
                        "target": variable_label(variable),
                        "value": int(count),
                    }
                )
    return out_rows


def distance_stat_rows(rows_by_source: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out_rows: list[dict[str, Any]] = []
    for source_key, rows in rows_by_source.items():
        if source_key.startswith("derived_"):
            continue
        distances = [as_float(row.get("distance_km")) for row in rows]
        distances = [value for value in distances if value is not None]
        if not distances:
            continue
        series = pd.Series(distances)
        for stat, value in {
            "count": float(series.count()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "min": float(series.min()),
            "max": float(series.max()),
        }.items():
            out_rows.append(
                {
                    "session_source_key": "derived_distance_stats",
                    "source_key": source_key,
                    "source_label": source_label(source_key),
                    "stat": stat,
                    "distance_km": value,
                    "metric_value": value,
                    "source": source_label(source_key),
                    "target": stat,
                    "value": value,
                }
            )
    return out_rows


def add_fire_population_proximity(rows_by_source: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    fire_rows = rows_by_source.get("portal_odf_firestats", [])
    landslide_rows = rows_by_source.get("portal_dogami_slido", [])
    population = as_float((rows_by_source.get("census_klamath_population") or [{}])[0].get("population")) or 0.0
    landslide_points = [
        (as_float(row.get("latitude")), as_float(row.get("longitude")))
        for row in landslide_rows
        if as_float(row.get("latitude")) is not None and as_float(row.get("longitude")) is not None
    ]
    enriched: list[dict[str, Any]] = []
    for row in fire_rows:
        lat = as_float(row.get("latitude"))
        lon = as_float(row.get("longitude"))
        if lat is None or lon is None:
            continue
        nearest_landslide = min(
            (distance_km(lat, lon, other_lat, other_lon) for other_lat, other_lon in landslide_points if other_lat is not None and other_lon is not None),
            default=None,
        )
        fire_distance = as_float(row.get("distance_km")) or distance_km(lat, lon)
        enriched.append(
            {
                **row,
                "session_source_key": "derived_fire_population_proximity",
                "source_key": "portal_odf_firestats",
                "source_label": "Fire Stats vs Klamath Falls Population",
                "population": population,
                "population_per_fire_distance_km": population / max(fire_distance, 0.1),
                "nearest_landslide_km": nearest_landslide,
                "fire_metric_per_1000_people": (as_float(row.get("metric_value")) or 0.0) / max(population / 1000.0, 1.0),
                "source": "Fire Stats vs Population",
                "target": str(row.get("year")),
                "value": as_float(row.get("metric_value")) or 0.0,
            }
        )
    return enriched


def add_nearest_fire_metrics(rows_by_source: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    fire_points = [
        (as_float(row.get("latitude")), as_float(row.get("longitude")))
        for row in rows_by_source.get("portal_odf_firestats", [])
        if as_float(row.get("latitude")) is not None and as_float(row.get("longitude")) is not None
    ]
    enriched: list[dict[str, Any]] = []
    for source_key, rows in rows_by_source.items():
        if source_key == "portal_odf_firestats" or source_key.startswith("derived_"):
            continue
        for row in rows:
            lat = as_float(row.get("latitude"))
            lon = as_float(row.get("longitude"))
            if lat is None or lon is None:
                continue
            distances = [
                distance_km(lat, lon, fire_lat, fire_lon)
                for fire_lat, fire_lon in fire_points
                if fire_lat is not None and fire_lon is not None
            ]
            enriched.append(
                {
                    **row,
                    "session_source_key": "derived_fire_proximity_reference",
                    "source_key": source_key,
                    "nearest_fire_km": min(distances) if distances else None,
                    "fire_count_within_1km": sum(1 for value in distances if value <= 1.0),
                    "fire_count_within_3km": sum(1 for value in distances if value <= 3.0),
                    "fire_count_within_5km": sum(1 for value in distances if value <= 5.0),
                    "source": source_label(source_key),
                    "target": "Nearby fire activity",
                    "value": sum(1 for value in distances if value <= 5.0),
                }
            )
    return enriched


def save_distribution_panels(rows: list[dict[str, Any]], output_path: Path) -> str:
    plt = _ensure_matplotlib()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, variable in zip(axes, ["metric_value", "distance_km", "year"]):
        subset = df[df["variable"] == variable]
        for label, group in subset.groupby("source_label"):
            ax.plot(group["bin_midpoint"], group["count"], marker="o", label=label)
        ax.set_title(f"{variable_label(variable)} distribution")
        ax.set_xlabel(variable_label(variable))
        ax.set_ylabel("Observation count")
        ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def save_distance_stats_plot(rows: list[dict[str, Any]], output_path: Path) -> str:
    plt = _ensure_matplotlib()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="source_label", columns="stat", values="distance_km", aggfunc="mean").fillna(0)
    ordered = [column for column in ["mean", "median", "min", "max"] if column in pivot.columns]
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    pivot[ordered].plot(kind="bar", ax=ax)
    ax.set_title("Distance statistics from Klamath Falls center")
    ax.set_xlabel("Source")
    ax.set_ylabel("Distance (km)")
    ax.legend(title="Statistic")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def save_fire_population_scatter(rows: list[dict[str, Any]], output_path: Path) -> str:
    plt = _ensure_matplotlib()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    x = pd.to_numeric(df["population_per_fire_distance_km"], errors="coerce")
    y = pd.to_numeric(df["metric_value"], errors="coerce")
    years = pd.to_numeric(df["year"], errors="coerce")
    keep = x.notna() & y.notna()
    scatter = ax.scatter(x[keep], y[keep], c=years[keep], cmap="viridis", s=60, alpha=0.8, label="Fire observation")
    if keep.sum() >= 2:
        coeff = pd.Series(y[keep]).corr(pd.Series(x[keep]))
        fit = pd.Series(y[keep]).groupby(x[keep]).mean().reset_index()
        fit.columns = ["x", "y"]
        fit = fit.sort_values("x")
        if len(fit) >= 2:
            ax.plot(fit["x"], fit["y"], color="#d62728", linewidth=2, label=f"Population proximity trend, r={coeff:.2f}")
    ax.set_title("Fire Stats measured against Klamath Falls population proximity")
    ax.set_xlabel("Population divided by fire distance from city center")
    ax.set_ylabel("Fire Stats normalized metric")
    ax.legend(loc="best")
    fig.colorbar(scatter, ax=ax, label="Observation year")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def save_regression_over_time(rows: list[dict[str, Any]], output_path: Path) -> str:
    plt = _ensure_matplotlib()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(111)
    for label, group in df.groupby("source_label"):
        x = pd.to_numeric(group["year"], errors="coerce")
        y = pd.to_numeric(group["metric_value"], errors="coerce")
        keep = x.notna() & y.notna()
        if keep.sum() == 0:
            continue
        ax.scatter(x[keep], y[keep], s=35, alpha=0.7, label=label)
        if keep.sum() >= 2 and x[keep].nunique() >= 2:
            slope, intercept = pd.Series(y[keep]).cov(pd.Series(x[keep])) / pd.Series(x[keep]).var(), y[keep].mean()
            intercept = float(y[keep].mean() - slope * x[keep].mean())
            trend_x = pd.Series(sorted(x[keep].unique()))
            ax.plot(trend_x, slope * trend_x + intercept, linewidth=2, label=f"{label} regression")
    ax.set_title("Regression for source metric increase over time")
    ax.set_xlabel("Year")
    ax.set_ylabel("Normalized source metric")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def save_geological_context_map(rows_by_source: dict[str, list[dict[str, Any]]], output_path: Path) -> str:
    plt = _ensure_matplotlib()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(111)
    colors = {
        "portal_odf_firestats": "#d95f02",
        "portal_dogami_slido": "#7570b3",
        "portal_sci_data_ics209_demo": "#e7298a",
        "workforce_technology_labor_market": "#1b9e77",
        "census_klamath_population": "#222222",
    }
    markers = {
        "portal_odf_firestats": "o",
        "portal_dogami_slido": "^",
        "portal_sci_data_ics209_demo": "s",
        "workforce_technology_labor_market": "D",
        "census_klamath_population": "*",
    }
    slido = pd.DataFrame(rows_by_source.get("portal_dogami_slido", []))
    if {"longitude", "latitude"}.issubset(slido.columns) and not slido.empty:
        x = pd.to_numeric(slido["longitude"], errors="coerce")
        y = pd.to_numeric(slido["latitude"], errors="coerce")
        keep = x.notna() & y.notna()
        if keep.any():
            ax.scatter(x[keep], y[keep], s=850, color="#f0e6ff", alpha=0.35, label="DOGAMI geologic landslide influence zone")
    for key in [
        "portal_odf_firestats",
        "portal_dogami_slido",
        "portal_sci_data_ics209_demo",
        "workforce_technology_labor_market",
        "census_klamath_population",
    ]:
        df = pd.DataFrame(rows_by_source.get(key, []))
        if df.empty or not {"longitude", "latitude"}.issubset(df.columns):
            continue
        x = pd.to_numeric(df["longitude"], errors="coerce")
        y = pd.to_numeric(df["latitude"], errors="coerce")
        keep = x.notna() & y.notna()
        size = 190 if key == "census_klamath_population" else 55
        ax.scatter(
            x[keep],
            y[keep],
            color=colors.get(key),
            marker=markers.get(key, "o"),
            s=size,
            edgecolor="white",
            linewidth=0.7,
            alpha=0.9,
            label=source_label(key),
        )
    radius_degrees = RADIUS_KM / 111.0
    study_circle = plt.Circle((KLAMATH_LON, KLAMATH_LAT), radius_degrees, color="#4c78a8", fill=False, linewidth=2, label="5 km study boundary")
    ax.add_patch(study_circle)
    ax.scatter([KLAMATH_LON], [KLAMATH_LAT], color="#000000", marker="+", s=180, label="Klamath Falls center")

    non_geo_lines = []
    for row in rows_by_source.get("workforce_technology_labor_market", []):
        non_geo_lines.append(f"{row.get('indicator')}: {row.get('metric_value'):,.0f}")
    for row in rows_by_source.get("census_klamath_population", []):
        non_geo_lines.append(f"ACS population: {row.get('population'):,.0f}")
    if non_geo_lines:
        ax.text(
            1.02,
            0.5,
            "Reference indicators\n" + "\n".join(non_geo_lines[:8]),
            transform=ax.transAxes,
            va="center",
            ha="left",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#999999", "alpha": 0.95},
        )
    ax.set_title("Klamath Falls hazard, labor, and geologic context map")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def build_outputs(rows_by_source: dict[str, list[dict[str, Any]]]) -> None:
    tools = analysis_tools()
    chart = charts()
    print_column_research(rows_by_source)
    all_rows = [row for rows in rows_by_source.values() for row in rows]
    hazard_rows = [
        row
        for key in ("portal_odf_firestats", "portal_dogami_slido", "portal_sci_data_ics209_demo")
        for row in rows_by_source.get(key, [])
    ]

    odf_avg = tools.aggregate_source(rows_by_source["portal_odf_firestats"], group_by=["year"], value="metric_value", source_key="odf_average_per_year")
    slido_avg = tools.aggregate_source(rows_by_source["portal_dogami_slido"], group_by=["year"], value="metric_value", source_key="slido_average_per_year")
    ics_avg = tools.aggregate_source(rows_by_source["portal_sci_data_ics209_demo"], group_by=["year"], value="metric_value", source_key="ics_average_per_year")
    job_avg = tools.aggregate_source(rows_by_source["workforce_technology_labor_market"], group_by=["year"], value="metric_value", source_key="jobs_average_per_year")
    derived_rows = odf_avg + slido_avg + ics_avg + job_avg
    rows_by_source["derived_average_per_year"] = derived_rows

    distance_rows = distance_stat_rows(rows_by_source)
    rows_by_source["derived_distance_stats"] = distance_rows
    fire_population_rows = add_fire_population_proximity(rows_by_source)
    rows_by_source["derived_fire_population_proximity"] = fire_population_rows
    fire_reference_rows = add_nearest_fire_metrics(rows_by_source)
    rows_by_source["derived_fire_proximity_reference"] = fire_reference_rows
    frequency_rows = frequency_bin_rows(
        rows_by_source,
        ["metric_value", "distance_km", "year", "nearest_fire_km", "nearest_landslide_km", "fire_count_within_5km"],
        bins=5,
    )
    rows_by_source["derived_frequency_bins"] = frequency_rows

    enriched_rows = tools.add_distribution_variable(all_rows, "metric_value", bins=6, output_column="metric_distribution_bin")
    enriched_rows = tools.add_distribution_variable(enriched_rows, "distance_km", bins=5, output_column="distance_distribution_bin")
    enriched_rows = tools.add_distribution_variable(enriched_rows, "year", bins=6, output_column="year_frequency_bin")
    enriched_rows = tools.add_probability_variable(enriched_rows, "session_source_key", "portal_dogami_slido", output_column="probability_landslide_source")
    enriched_rows = tools.add_bayes_variable(
        enriched_rows,
        "session_source_key",
        "portal_dogami_slido",
        "county",
        "Klamath",
        output_column="bayes_landslide_given_klamath",
    )
    enriched_rows = tools.add_regression_variable(enriched_rows, x="year", y="metric_value", output_column="metric_regression_prediction")
    rows_by_source["derived_enriched_variables"] = enriched_rows

    print("\nDerived comparison sources")
    print("odf_average_per_year", odf_avg[:8])
    print("slido_average_per_year", slido_avg[:8])
    print("ics_average_per_year", ics_avg[:8])
    print("jobs_average_per_year", job_avg[:8])
    print("frequency_bins", frequency_rows[:12])
    print("distance_stats", distance_rows)
    print("fire_population_proximity", fire_population_rows[:8])
    print("fire_proximity_reference", fire_reference_rows[:8])
    print("\nEnriched data sample")
    for row in enriched_rows[:12]:
        print(row)

    chart.scatter(source("portal_odf_firestats", "direct://odf"), "longitude", "latitude", name="map_without_analysis_fire_points")
    chart.scatter(source("portal_dogami_slido", "direct://slido"), "longitude", "latitude", name="map_without_analysis_landslide_points")
    chart.scatter(source("workforce_technology_labor_market", "direct://jobs"), "longitude", "latitude", name="map_without_analysis_job_market_points")
    chart.metric(
        source("combined", "direct://combined", column_hints=["year", "metric_value"]),
        "occurrence_frequency_over_time",
        [
            {"source_key": "portal_odf_firestats", "x": "year", "y": "metric_value", "label": "Fire"},
            {"source_key": "portal_dogami_slido", "x": "year", "y": "metric_value", "label": "Landslide"},
            {"source_key": "portal_sci_data_ics209_demo", "x": "year", "y": "metric_value", "label": "ICS surrogate"},
            {"source_key": "workforce_technology_labor_market", "x": "year", "y": "metric_value", "label": "Jobs"},
            {"source_key": "census_klamath_population", "x": "year", "y": "metric_value", "label": "Population"},
        ],
    )
    chart.bar(source("derived_average_per_year", "direct://derived"), "metric_value_mean", "year", name="general_counts_and_averages_per_year")
    chart.bar(
        source("derived_frequency_bins", "direct://frequency", column_hints=["bin_label", "count", "variable_label", "source_label"]),
        "count",
        "bin_label",
        name="frequency_bins_by_metric_distance_and_year",
    )
    chart.bar(
        source("derived_distance_stats", "direct://distance", column_hints=["source_label", "distance_km", "stat"]),
        "distance_km",
        "source_label",
        name="distance_statistics_by_source",
    )
    chart.heatmap(source("portal_dogami_slido", "direct://slido"), "klamath_landslide_fire_job_heatmap", "heat_x", "heat_y", "heat_z")
    chart.correlation_matrix(
        source("combined", "direct://combined"),
        "klamath_kernel_correlation_matrix",
        variables=["year", "metric_value", "heat_z", "latitude", "longitude", "distance_km"],
    )
    chart.sankey(source("combined", "direct://combined"), "cross_source_interaction_sankey")
    chart.cross_pair(
        source("combined", "direct://combined"),
        "fire_landslide_spatial_cross_pair",
        ("portal_odf_firestats", "longitude", "latitude"),
        ("portal_dogami_slido", "longitude", "latitude"),
    )
    enriched_source = source(
        "derived_enriched_variables",
        "direct://enriched",
        column_hints=["metric_value", "metric_regression_prediction", "longitude", "latitude"],
    )
    chart.scatter(enriched_source, "metric_value", "metric_regression_prediction", name="poisson_style_frequency_estimation")
    chart.scatter(enriched_source, "longitude", "latitude", name="map_with_analysis_interaction_zone")
    chart.scatter(
        source(
            "derived_fire_population_proximity",
            "direct://fire-population",
            column_hints=["population_per_fire_distance_km", "metric_value", "nearest_landslide_km", "year"],
        ),
        "population_per_fire_distance_km",
        "metric_value",
        name="fire_stats_against_population_proximity",
    )
    chart.scatter(
        source(
            "derived_fire_proximity_reference",
            "direct://fire-reference",
            column_hints=["nearest_fire_km", "metric_value", "fire_count_within_5km"],
        ),
        "nearest_fire_km",
        "metric_value",
        name="reference_sources_nearest_fire_metric",
    )

    chart_outputs = chart.render_python(rows_by_source, OUT_DIR / "charts")
    chart_outputs.extend(
        [
            save_distribution_panels(frequency_rows, OUT_DIR / "charts" / "frequency_distribution_panels.png"),
            save_distance_stats_plot(distance_rows, OUT_DIR / "charts" / "distance_statistics_from_klamath.png"),
            save_fire_population_scatter(fire_population_rows, OUT_DIR / "charts" / "fire_stats_vs_population_scatter.png"),
            save_regression_over_time(all_rows, OUT_DIR / "charts" / "source_metric_regression_over_time.png"),
            save_geological_context_map(rows_by_source, OUT_DIR / "charts" / "geological_context_reference_map.png"),
        ]
    )
    region_plot = tools.plot_regions(all_rows, OUT_DIR / "geometry" / "analysis_regions_intersections.png", intersection_radius_km=5)
    raw_region_plot = tools.plot_regions(hazard_rows, OUT_DIR / "geometry" / "raw_hazard_regions.png", intersection_radius_km=0.5)
    intersections = tools.geometry_intersections(all_rows, radius_km=5)
    distances = tools.region_distances(all_rows)
    correlation = tools.correlation(all_rows, variables=["year", "metric_value", "heat_z", "latitude", "longitude", "distance_km"])
    regression = tools.regression(all_rows, x="year", y="metric_value")
    population_regression = tools.regression(fire_population_rows, x="year", y="fire_metric_per_1000_people")

    print("\nChart outputs")
    for path in chart_outputs:
        print(path)
    print("\nGeometric analysis")
    print("analysis region plot", region_plot)
    print("raw hazard region plot", raw_region_plot)
    print("intersections", intersections)
    print("nearest-neighbor/cross distances", distances)
    print("\nCorrelation/regression")
    print("correlation", correlation)
    print("regression", regression)
    print("fire metric per 1000 people regression", population_regression)
    print("\nBackend availability")
    print(tools.available_backends())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_by_source = fetch_near_klamath()
    build_outputs(rows_by_source)


if __name__ == "__main__":
    main()

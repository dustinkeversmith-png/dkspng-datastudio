"""
Project 2 — Regional Multi-Source Integration & Analysis
=========================================================

Phase 1  Register sources, fetch, distance-filter, collect metadata.
Phase 2  Sampling diagnostics, KNN/KMeans, cross-source models,
         whole-group ARIMA/Decision-Tree/PCA/Fourier, advanced plots,
         visual descriptors.

Study centre: Klamath Falls, OR
Run from the repo root:
    python project_2.py
"""
from __future__ import annotations

import json
import math
import os
from typing import Any

import pandas as pd

from backend.schemas import SourceDefinition
from backend.source_registry import add_or_update_source, get_source
from backend.workflow.source_binding import source as make_source

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRANTS_PASS_LAT = 42.4393
GRANTS_PASS_LON = -123.3284

# Aliases used throughout the module
CENTRE_LAT = GRANTS_PASS_LAT
CENTRE_LON = GRANTS_PASS_LON
QUERY_RADIUS_MI = 50
PLOT_DIR = os.path.join("data", "plots", "Grants Pass")


PORTAL_APIS: dict[str, dict[str, str]] = {
    "odf_firestats": {
        "open_data_csv": "https://data.oregon.gov/resource/fa7z-shhx.csv",
    },
    "sci_data_ics209": {
        "csv_demo_surrogate": "https://data.oregon.gov/resource/fa7z-shhx.csv",
    },
}

# Variables of interest per source (numeric focus)
VARS: dict[str, list[str]] = {
    "noaa_gsod": ["TEMP", "GUST", "PRCP", "VISIB"],
    "epa_air_quality": ["AQI"],
    "portal_odf_firestats": ["esttotalacres"],
    "portal_dogami_slido": ["AREA_ft2", "VOLUME_ft3"],
    "nifc_wildfire_incidents": ["IncidentSize"],
}

# Human-readable dataset names
DISPLAY_NAMES: dict[str, str] = {
    "noaa_gsod": "NOAA Daily Weather (Medford, OR)",
    "epa_air_quality": "EPA Air Quality Index",
    "portal_odf_firestats": "ODF Fire Statistics",
    "portal_dogami_slido": "DOGAMI Landslide Database",
    "nifc_wildfire_incidents": "NIFC Wildfire Incidents",
    "portal_sci_data_ics209_demo": "ICS-209 Fire Reports",
    "emsi_labor_postings": "EMSI Labor Postings",
    "dol_h1b_records": "DoL H-1B Records",
}

# Physical units for each variable
UNITS: dict[str, str] = {
    "TEMP": "°F",
    "GUST": "mph",
    "PRCP": "in",
    "VISIB": "mi",
    "AQI": "index (0–500)",
    "esttotalacres": "acres",
    "IncidentSize": "acres",
    "EstimatedCostToDate": "USD",
    "AREA_ft2": "ft²",
    "VOLUME_ft3": "ft³",
    "DEEP_SHAL": "depth category",
    "CONTR_FACT": "contributing factor",
}

# ---------------------------------------------------------------------------
# Source registration
# ---------------------------------------------------------------------------

def register_datasources() -> None:
    """Upsert all project-2 sources into the in-memory registry."""

    add_or_update_source(SourceDefinition(
        source_key="nifc_wildfire_incidents",
        display_name="NIFC Wildfire Incidents (ArcGIS REST)",
        category="natural_hazards", connector_type="arcgis_rest",
        source_url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query",
        notes="NIFC WFIGS incident locations. Auth: None.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="noaa_gsod",
        display_name="NOAA Global Surface Summary (CSV)",
        category="weather", connector_type="csv",
        source_url="https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2023/72219013874.csv",
        requires_download=True,
        notes="Station 72219013874 (Medford, OR) daily summary 2023.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="epa_air_quality",
        display_name="EPA AQS Daily AQI by County 2023",
        category="environmental", connector_type="csv",
        source_url="https://aqs.epa.gov/aqsweb/airdata/daily_aqi_by_county_2023.zip",
        requires_download=True,
        notes="ZIP → CSV. county-level daily AQI.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="portal_odf_firestats",
        display_name="ODF Fire Statistics (data.oregon.gov)",
        category="natural_disasters", connector_type="csv",
        source_url=PORTAL_APIS["odf_firestats"]["open_data_csv"],
        notes="Socrata API. Auth: None.",
        latitude_fields=["lat_dd", "latitude", "lat"],
        longitude_fields=["long_dd", "longitude", "lon"],
    ))

    add_or_update_source(SourceDefinition(
        source_key="portal_dogami_slido",
        display_name="DOGAMI SLIDO (ArcGIS REST)",
        category="natural_disasters", connector_type="arcgis_rest",
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
        notes="Layer 0 of the SLIDO42 MapServer. Auth: None.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="portal_sci_data_ics209_demo",
        display_name="ICS-209-PLUS / Sci Data 2023 (surrogate)",
        category="research_reference", connector_type="csv",
        source_url=PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"],
        notes="CSV surrogate. Auth: None.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="emsi_labor_postings",
        display_name="EMSI Labor Postings",
        category="labor_market", connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv",
        notes="Surrogate. Auth: API key.",
    ))

    add_or_update_source(SourceDefinition(
        source_key="dol_h1b_records",
        display_name="DoL H-1B Disclosure Data",
        category="labor_market", connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv",
        notes="Surrogate. Auth: None.",
    ))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _filter_by_distance(df: pd.DataFrame, lat_col: str, lon_col: str,
                        clat: float, clon: float, radius_mi: float) -> pd.DataFrame:
    if lat_col not in df.columns or lon_col not in df.columns:
        return df
    df = df.copy()
    df["_dist_mi"] = df.apply(
        lambda r: _haversine_mi(clat, clon, float(r[lat_col]), float(r[lon_col]))
        if pd.notna(r[lat_col]) and pd.notna(r[lon_col]) else float("inf"),
        axis=1,
    )
    return df[df["_dist_mi"] <= radius_mi].drop(columns=["_dist_mi"])


def _find_lat_lon_cols(df: pd.DataFrame, definition: SourceDefinition) -> tuple[str | None, str | None]:
    lat = next((c for c in definition.latitude_fields if c in df.columns), None)
    lon = next((c for c in definition.longitude_fields if c in df.columns), None)
    return lat, lon


# ---------------------------------------------------------------------------
# Phase 1 — fetch all sources
# ---------------------------------------------------------------------------

_ALL_SOURCE_KEYS = [
    "nifc_wildfire_incidents",
    "noaa_gsod",
    "epa_air_quality",
    "portal_odf_firestats",
    "portal_dogami_slido",
    "portal_sci_data_ics209_demo",
    "emsi_labor_postings",
    "dol_h1b_records",
]


def test_all_sources() -> tuple[list[dict[str, Any]], dict[str, pd.DataFrame]]:
    """Fetch and metadata-profile each source. Return (report_list, dataframes_dict)."""
    from backend.metadata_analyzer.analyzer import MetadataAnalyzer

    combined: list[dict[str, Any]] = []
    dataframes: dict[str, pd.DataFrame] = {}

    for key in _ALL_SOURCE_KEYS:
        print(f"\n── {key} ──")
        record: dict[str, Any] = {
            "source_key": key, "status": "error",
            "rows_total": 0, "rows_in_radius": 0, "columns": [],
            "metadata": {}, "error": None,
        }
        try:
            definition = get_source(key)
            s = make_source(definition)
            df = s.dataframes.get(key)
            if df is None or df.empty:
                record["status"] = "empty"
                print("  ⚠  No data returned.")
                combined.append(record)
                continue

            record["rows_total"] = len(df)
            record["columns"] = list(df.columns)

            lat_col, lon_col = _find_lat_lon_cols(df, definition)
            if lat_col and lon_col:
                filtered = _filter_by_distance(df, lat_col, lon_col,
                                               GRANTS_PASS_LAT, GRANTS_PASS_LON, QUERY_RADIUS_MI)
            else:
                filtered = df
            record["rows_in_radius"] = len(filtered)

            sample = filtered.head(100).to_dict(orient="records")
            analyzer = MetadataAnalyzer(source_key=key, source_url=definition.source_url)
            record["metadata"] = analyzer.generate_profile(sample).model_dump()
            record["status"] = "ok"
            dataframes[key] = filtered   # store radius-filtered data for all downstream analysis
            print(f"  ✓  {len(df)} rows total | {len(filtered)} within {QUERY_RADIUS_MI} mi")

        except Exception as exc:
            record["error"] = str(exc)
            print(f"  ✗  {exc}")

        combined.append(record)

    return combined, dataframes


# ---------------------------------------------------------------------------
# Phase 2 — sampling diagnostics
# ---------------------------------------------------------------------------

def run_sampling_analysis(dataframes: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    from backend.sampling.sampling_engine import SamplingEngine

    sampling_records: list[dict[str, Any]] = []

    sampling_targets = {
        "noaa_gsod": {"targets": ["TEMP", "GUST", "PRCP", "VISIB"],
                      "bias_cond": None},
        "epa_air_quality": {"targets": ["AQI"],
                            "bias_cond": {"field": "State Name", "op": "==", "value": "Oregon"}},
        "portal_odf_firestats": {"targets": ["esttotalacres"],
                                 "bias_cond": {"field": "county", "op": "==", "value": "Josephine"}},
        "portal_dogami_slido": {"targets": ["AREA_ft2", "VOLUME_ft3"],
                                "bias_cond": None},
        "nifc_wildfire_incidents": {"targets": ["IncidentSize"],
                                    "bias_cond": None},
    }

    print("\n=== Sampling Analysis ===")
    for key, spec in sampling_targets.items():
        df = dataframes.get(key)
        if df is None or df.empty:
            continue

        engine = SamplingEngine(df, key)

        for target in spec["targets"]:
            # Uncertainty
            unc = engine.uncertainty_if(target, sample_size=200, confidence=0.95, method="bootstrap")
            print(f"  [{key}] {target} uncertainty: {unc.uncertainty} CI={unc.confidence_interval}")
            sampling_records.append(unc.to_dict())

            # Confidence interval
            ci = engine.confidence_interval(target, confidence=0.95, method="t_interval")
            sampling_records.append(ci.to_dict())

        # Bias check
        if spec["bias_cond"]:
            bias = engine.bias_if(spec["bias_cond"], target=spec["targets"][0])
            print(f"  [{key}] bias_score={bias.bias_score}")
            sampling_records.append(bias.to_dict())

    return sampling_records


# ---------------------------------------------------------------------------
# Phase 2 — fuse sources + KNN / KMeans
# ---------------------------------------------------------------------------

def fuse_sources(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Concatenate all DataFrames into one with a source_key column."""
    frames: list[pd.DataFrame] = []
    for key, df in dataframes.items():
        chunk = df.copy()
        chunk["__source__"] = key
        frames.append(chunk)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    print(f"\n  [Fusion] {len(combined)} rows from {len(frames)} sources")
    return combined


def run_knn(df: pd.DataFrame) -> Any:
    from backend.neighbors.neighbor_engine import NeighborEngine
    from backend.neighbors.spatial_temporal_distance import infer_stkey

    # Here the goal is to pass it specific keys in which to measure distances too, for example
    # You would say
    # {"time": "YEAR",} from all of the different datasets, then are able to sample the data, by time or space proximity to each other.

    print("\n=== KNN Spatial-Temporal ===")
    if df.empty:
        return None
    engine = NeighborEngine(df, "combined")
    st_key = infer_stkey(list(df.columns))
    result = engine.knn(k=5, st_key=st_key)
    print(f"  k={result.n_neighbors} | features={result.feature_fields} | rows={result.metadata.get('n_rows')}")
    return result


def run_kmeans(df: pd.DataFrame, k: int = 6) -> Any:
    from backend.clustering.cluster_engine import ClusterEngine

    print("\n=== KMeans Clustering ===")
    if df.empty:
        return None
    engine = ClusterEngine(df, "combined")
    result = engine.kmeans(k=k)
    print(f"  k={result.k} | inertia={result.inertia} | silhouette={result.silhouette_score}")
    return result


# ---------------------------------------------------------------------------
# Phase 2 — cross-source analysis
# ---------------------------------------------------------------------------

def run_cross_analysis(dataframes: dict[str, pd.DataFrame]) -> Any:
    from backend.cross_analysis.cross_analysis_spec import CrossAnalysisSpec
    from backend.cross_analysis.cross_analysis_engine import CrossAnalysisEngine

    print("\n=== Cross-Source Analysis ===")
    combined_df = fuse_sources(dataframes)
    if combined_df.empty:
        return None

    # For the cross analyis measure GUST and PRCP and AQI vs fire incident rates,
    # And also create aditional anaylsis for multiple other combinations of features, possibly
    # Project or color the backgrounds for the background variables.
 
    spec = CrossAnalysisSpec(
        grouping="kmeans_cluster",
        variable_groups={
            "weather":    ["TEMP", "GUST", "PRCP", "VISIB"],
            "air_quality": ["AQI"],
            "fire":       ["esttotalacres"],
            "landslide":  ["AREA_ft2", "VOLUME_ft3"],
        },
        models=["linear_regression", "logistic_regression", "svm", "naive_bayes"],
    )


    # For each of these analysis make predictions and plot accuracy metrics vs eachother
    

    os.makedirs(PLOT_DIR, exist_ok=True)
    engine = CrossAnalysisEngine(combined_df, "combined", plot_dir=PLOT_DIR)
    result = engine.run(spec)
    print(f"  {result.summary.get('total_runs')} runs | {result.summary.get('successful_runs')} ok")
    return result


# ---------------------------------------------------------------------------
# Phase 2 — whole-group analysis
# ---------------------------------------------------------------------------

def run_whole_group_analysis(dataframes: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    from backend.models.model_engine import ModelEngine

    print("\n=== Whole-Group Analysis ===")
    results: list[dict[str, Any]] = []
    os.makedirs(PLOT_DIR, exist_ok=True)

    # measure temp, prcb, gust, and visib vs fire size

    whole_jobs = [
        # (source_key, model_key, features, target)
        ("noaa_gsod", "arima", ["TEMP"], None),
        ("noaa_gsod", "fourier", ["TEMP"], None),
        ("noaa_gsod", "pca", ["TEMP", "GUST", "PRCP", "VISIB"], None),
        ("portal_odf_firestats", "decision_tree", ["esttotalacres"], "specificcause"),
        ("portal_dogami_slido", "decision_tree", ["AREA_ft2", "VOLUME_ft3", "DEEP_SHAL"], "CONTR_FACT"),
        ("nifc_wildfire_incidents", "linear_regression", ["IncidentSize"], "EstimatedCostToDate"),
    ]

    for src_key, model_key, features, target in whole_jobs:
        df = dataframes.get(src_key)
        if df is None or df.empty:
            continue
        engine = ModelEngine(df, src_key)
        result = engine.run(
            model_key=model_key, features=features, target=target,
            plot=True, extra_context={"plot_dir": PLOT_DIR, "forecast_steps": 14},
        )
        status = "ok" if not result.metadata.get("error") and not result.metadata.get("warning") else "warn"
        print(f"  [{status}] {model_key} on {src_key} | metrics={result.metrics}")
        results.append(result.to_dict())

    return results


# ---------------------------------------------------------------------------
# Phase 2 — distribution plots per source variable
# ---------------------------------------------------------------------------

def generate_distribution_plots(dataframes: dict[str, pd.DataFrame]) -> list[str]:
    """One summary figure per source (hist + box for each numeric variable)."""
    from backend.advanced_plots.plot_engine import source_summary_plot

    print("\n=== Distribution Summary Plots ===")
    os.makedirs(PLOT_DIR, exist_ok=True)
    paths: list[str] = []

    for src_key, cols in VARS.items():
        df = dataframes.get(src_key)
        if df is None or df.empty:
            continue
        display = DISPLAY_NAMES.get(src_key, src_key)
        try:
            path = source_summary_plot(
                df, cols, display, UNITS, PLOT_DIR, tag=src_key,
            )
            if path:
                paths.append(path)
                print(f"  ✓  {display}")
        except Exception as e:
            print(f"  ✗  {src_key}: {e}")

    return paths


# ---------------------------------------------------------------------------
# Phase 2 — cross-correlation analysis
# ---------------------------------------------------------------------------

def generate_cross_correlation_plots(dataframes: dict[str, pd.DataFrame]) -> list[str]:
    """
    For every pair of numeric variables across all sources:
      1. Build per-source correlation matrix and plot heatmap.
      2. Build a cross-source correlation matrix from aggregated statistics.
      3. Plot scatter + regression for every cross-source variable pair.
    """
    from backend.advanced_plots.plot_engine import (
        cross_correlation_heatmap, all_pairs_scatter_grid, cross_variable_scatter,
    )
    import numpy as np
    import itertools

    print("\n=== Cross-Correlation Plots ===")
    os.makedirs(PLOT_DIR, exist_ok=True)
    paths: list[str] = []

    # ---- Step 1: collect all numeric series, keyed as "source/variable" ----
    all_series: dict[str, pd.Series] = {}
    for src_key, cols in VARS.items():
        df = dataframes.get(src_key)
        if df is None or df.empty:
            continue
        for col in cols:
            if col not in df.columns:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna().reset_index(drop=True)
            if len(s) < 5:
                continue
            key = f"{src_key}/{col}"
            all_series[key] = s

    if len(all_series) < 2:
        print("  ⚠  Not enough numeric series for cross-correlation")
        return paths

    # Drop constant (zero-variance) series — these cause NaN corrcoef / polyfit crashes
    all_series = {k: s for k, s in all_series.items() if s.std() > 1e-10}
    if len(all_series) < 2:
        print("  ⚠  All series are constant — cannot compute correlations")
        return paths


    # Build display labels and units
    disp: dict[str, str] = {}
    unit_map: dict[str, str] = {}
    for k in all_series:
        src_key, col = k.split("/", 1)
        src_display = DISPLAY_NAMES.get(src_key, src_key)
        unit = UNITS.get(col, "")
        disp[k] = f"{src_display}\n{col}"
        unit_map[col] = unit

    # ---- Step 2: per-source correlation matrix ----
    for src_key, cols in VARS.items():
        src_keys_in = [f"{src_key}/{c}" for c in cols if f"{src_key}/{c}" in all_series]
        if len(src_keys_in) < 2:
            continue
        src_df = pd.concat(
            [all_series[k].rename(k.split("/", 1)[1]) for k in src_keys_in], axis=1
        )
        corr = src_df.corr()
        display = DISPLAY_NAMES.get(src_key, src_key)
        try:
            path = cross_correlation_heatmap(
                corr, f"Within-Source Correlations — {display}",
                PLOT_DIR, tag=f"within_{src_key}",
            )
            paths.append(path)
            print(f"  ✓  within-source corr: {display}")
        except Exception as e:
            print(f"  ✗  within-source corr {src_key}: {e}")

    # ---- Step 3: cross-source correlation matrix (aggregated stats) ----
    # Align on common index by sampling to min length
    keys = list(all_series.keys())
    min_len = min(len(s) for s in all_series.values())
    sample_size = min(min_len, 500)

    aligned: dict[str, pd.Series] = {}
    for k, s in all_series.items():
        aligned[k] = s.sample(n=sample_size, random_state=42).reset_index(drop=True)

    aligned_df = pd.DataFrame(aligned)
    aligned_df.columns = [k.split("/", 1)[1] + "\n(" + DISPLAY_NAMES.get(k.split("/")[0], k.split("/")[0])[:12] + ")" for k in keys]
    corr_all = aligned_df.corr()

    try:
        path = cross_correlation_heatmap(
            corr_all, "Cross-Source Correlation Matrix (sampled)",
            PLOT_DIR, tag="cross_source_all",
        )
        paths.append(path)
        print(f"  ✓  cross-source correlation matrix ({len(keys)} variables)")
    except Exception as e:
        print(f"  ✗  cross-source corr matrix: {e}")

    # ---- Step 4: scatter plot for every cross-source pair ----
    cross_pairs = [
        (a, b) for a, b in itertools.combinations(keys, 2)
        if a.split("/")[0] != b.split("/")[0]  # only cross-source pairs
    ]
    print(f"  Generating {len(cross_pairs)} cross-source scatter plots…")

    for xk, yk in cross_pairs:
        xs = aligned[xk].values.tolist() if xk in aligned else all_series[xk].sample(
            min(len(all_series[xk]), sample_size), random_state=42).tolist()
        ys = aligned[yk].values.tolist() if yk in aligned else all_series[yk].sample(
            min(len(all_series[yk]), sample_size), random_state=42).tolist()

        try:
            r = float(np.corrcoef(xs, ys)[0, 1])
        except Exception:
            r = float("nan")

        x_src, x_col = xk.split("/", 1)
        y_src, y_col = yk.split("/", 1)
        x_unit = UNITS.get(x_col, "")
        y_unit = UNITS.get(y_col, "")
        xl = f"{x_col}" + (f" ({x_unit})" if x_unit else "") + f"\n— {DISPLAY_NAMES.get(x_src, x_src)}"
        yl = f"{y_col}" + (f" ({y_unit})" if y_unit else "") + f"\n— {DISPLAY_NAMES.get(y_src, y_src)}"
        t = f"{x_col} vs {y_col}"
        safe_tag = f"{x_src}_{x_col}__vs__{y_src}_{y_col}"

        try:
            path = cross_variable_scatter(
                xs, ys, xl, yl, title=t, plot_dir=PLOT_DIR,
                tag=safe_tag, pearson_r=r,
            )
            if path:
                paths.append(path)
        except Exception as e:
            print(f"  ✗  scatter {safe_tag}: {e}")

    # ---- Step 5: within-source scatter grids ----
    for src_key, cols in VARS.items():
        src_keys_in = [f"{src_key}/{c}" for c in cols if f"{src_key}/{c}" in all_series]
        if len(src_keys_in) < 2:
            continue
        src_aligned = {k: aligned.get(k, all_series[k].sample(
            min(len(all_series[k]), sample_size), random_state=42).reset_index(drop=True))
            for k in src_keys_in}
        new_paths = all_pairs_scatter_grid(
            src_aligned, disp, UNITS,
            title=DISPLAY_NAMES.get(src_key, src_key),
            plot_dir=PLOT_DIR, tag=f"within_{src_key}",
        )
        paths.extend(new_paths)

    cross_count = len([p for p in paths if "__vs__" in p])
    print(f"  ✓  {len(paths)} total correlation plots ({cross_count} cross-source scatter)")
    return paths


# ---------------------------------------------------------------------------
# Phase 2 — cluster map plot
# ---------------------------------------------------------------------------

def generate_cluster_plots(
    df: pd.DataFrame,
    cluster_result: Any,
) -> list[str]:
    from backend.advanced_plots.plot_engine import cluster_map

    paths: list[str] = []
    if cluster_result is None or df.empty:
        return paths
    os.makedirs(PLOT_DIR, exist_ok=True)

    lat = next((c for c in ["latitude", "lat", "lat_dd", "LATITUDE"] if c in df.columns), None)
    lon = next((c for c in ["longitude", "lon", "long_dd", "LONGITUDE"] if c in df.columns), None)
    if lat and lon and cluster_result.labels:
        try:
            path = cluster_map(
                df, lat, lon, cluster_result.labels,
                f"KMeans k={cluster_result.k} — Combined Sources",
                PLOT_DIR, tag="combined",
            )
            paths.append(path)
            print(f"  ✓  cluster map → {path}")
        except Exception as e:
            print(f"  ✗  cluster map: {e}")
    return paths


# ---------------------------------------------------------------------------
# Phase 2 — sampling diagnostic plots
# ---------------------------------------------------------------------------

def generate_sampling_plots(sampling_records: list[dict[str, Any]]) -> list[str]:
    from backend.advanced_plots.plot_engine import (
        confidence_interval_plot_grouped, sampling_bias_plot,
    )

    paths: list[str] = []
    os.makedirs(PLOT_DIR, exist_ok=True)
    print("\n=== Sampling Diagnostic Plots ===")

    # CI plot — grouped by source, one panel each
    ci_records = [
        r for r in sampling_records
        if r.get("confidence_interval") and r.get("method") != "bias_if"
    ]
    if ci_records:
        try:
            path = confidence_interval_plot_grouped(
                ci_records, DISPLAY_NAMES, UNITS, PLOT_DIR, tag="all_sources",
            )
            if path:
                paths.append(path)
                print(f"  ✓  grouped CI plot → {path}")
        except Exception as e:
            print(f"  ✗  grouped CI plot: {e}")

    # Bias plots
    bias_records = [r for r in sampling_records if r.get("method") == "bias_if" and r.get("metadata")]
    for b in bias_records:
        meta = b.get("metadata", {})
        if meta.get("group_mean") is None:
            continue
        cond = meta.get("condition", {})
        src_key = b["source_key"]
        target = b.get("target") or "value"
        unit = UNITS.get(target, "")
        display = DISPLAY_NAMES.get(src_key, src_key)
        group_label = f"{cond.get('field')} = {cond.get('value')}"
        try:
            path = sampling_bias_plot(
                meta["group_mean"], meta["complement_mean"],
                group_label, "All Other Records",
                title=f"Sampling Bias Check — {display} / {target}",
                plot_dir=PLOT_DIR,
                tag=f"{src_key}_{target}",
                unit=unit,
                variable=target,
            )
            paths.append(path)
            print(f"  ✓  bias plot: {display}/{target}")
        except Exception as e:
            print(f"  ✗  bias plot {src_key}: {e}")

    return paths



# ---------------------------------------------------------------------------
# Phase 2 — visual descriptors
# ---------------------------------------------------------------------------

def generate_visual_descriptors(
    model_results: list[dict[str, Any]],
    cluster_result: Any,
    sampling_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from backend.visual_ops.neural_descriptor_generator import NeuralDescriptorGenerator
    from backend.models.model_result import ModelResult

    gen = NeuralDescriptorGenerator()
    descriptors: list[dict[str, Any]] = []

    if cluster_result:
        desc = gen.from_cluster_result(cluster_result, source_key="combined")
        descriptors.append(desc.to_dict())

    for rec in model_results[:5]:  # cap at 5 for brevity
        mr = ModelResult(
            model_key=rec["model_key"],
            task_type=rec["task_type"],
            source_key=rec["source_key"],
            feature_fields=rec["feature_fields"],
            target_field=rec["target_field"],
            metrics=rec["metrics"],
        )
        desc = gen.from_model_result(mr)
        descriptors.append(desc.to_dict())

    print(f"\n  ✓  {len(descriptors)} visual descriptors generated")
    return descriptors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def project2() -> None:
    print("=" * 60)
    print("Project 2 — Regional Data Studio Integration & Analysis")
    print(f"Centre: Grants Pass, OR  ({GRANTS_PASS_LAT}, {GRANTS_PASS_LON})")
    print(f"Radius: {QUERY_RADIUS_MI} miles")
    print("=" * 60)

    # ── Phase 1: Register and fetch ─────────────────────────────────────
    register_datasources()
    metadata_records, dataframes = test_all_sources()

    os.makedirs("data", exist_ok=True)
    os.makedirs(PLOT_DIR, exist_ok=True)
    metadata_path = os.path.join(PLOT_DIR, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_records, f, indent=4, default=str)

    ok_sources = {k: v for k, v in dataframes.items()}
    print(f"\n  {len(ok_sources)} sources loaded successfully")

    # ── Phase 2a: Sampling diagnostics ─────────────────────────────
    sampling_records = run_sampling_analysis(ok_sources)

    # ── Phase 2b: Fuse + KNN + KMeans ─────────────────────────────
    combined_df = fuse_sources(ok_sources)



    
    neighbor_result = run_knn(combined_df)

    # Create a plot from the neighbor result, test few different source points to see if it predicts the dataset.

    # Show a plot of the neighbor hoods for different points in the original data, color code each dot by what original dataset it came from
    

    cluster_result = run_kmeans(combined_df, k=6)

    # Break the data into each cluster and run the analysis and charting for each group

    # ── Phase 2c: Cross-source ML models ─────────────────────────
    cross_result = run_cross_analysis(ok_sources)

    # ── Phase 2d: Whole-group models ─────────────────────────────
    whole_results = run_whole_group_analysis(ok_sources)

    # ── Phase 2e: Distribution summary plots (1 per source) ─────────
    dist_plot_paths = generate_distribution_plots(ok_sources)

    # ── Phase 2e2: Cross-correlation analysis & plots ─────────────
    corr_plot_paths = generate_cross_correlation_plots(ok_sources)

    # ── Phase 2f: Cluster map ──────────────────────────────────
    cluster_plot_paths = generate_cluster_plots(combined_df, cluster_result)

    # ── Phase 2g: Sampling diagnostic plots ─────────────────────
    sampling_plot_paths = generate_sampling_plots(sampling_records)

    # ── Phase 2h: Visual descriptors ────────────────────────────
    descriptors = generate_visual_descriptors(whole_results, cluster_result, sampling_records)

    # ── Final report ───────────────────────────────────────────
    all_plot_paths = dist_plot_paths + corr_plot_paths + cluster_plot_paths + sampling_plot_paths
    report = {
        "metadata": metadata_records,
        "sampling": sampling_records,
        "cluster": cluster_result.to_dict() if cluster_result else None,
        "cross_analysis": cross_result.to_dict() if cross_result else None,
        "whole_group_models": whole_results,
        "visual_descriptors": descriptors,
        "plot_paths": all_plot_paths,
        "plot_counts": {
            "distribution": len(dist_plot_paths),
            "cross_correlation": len(corr_plot_paths),
            "cluster": len(cluster_plot_paths),
            "sampling": len(sampling_plot_paths),
        },
    }

    report_path = os.path.join(PLOT_DIR, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, default=str)

    print(f"\n{'=' * 60}")
    print(f"Done — {len(ok_sources)} sources")
    print(f"  Distribution plots : {len(dist_plot_paths)}")
    print(f"  Cross-corr plots   : {len(corr_plot_paths)}")
    print(f"  Cluster plots      : {len(cluster_plot_paths)}")
    print(f"  Sampling plots     : {len(sampling_plot_paths)}")
    print(f"  Total plots        : {len(all_plot_paths)} → {PLOT_DIR}/")
    print(f"Report → {os.path.abspath(report_path)}")



if __name__ == "__main__":
    project2()

import json
import math
import sys
from pathlib import Path

import pandas as pd


def _numeric_series(df: pd.DataFrame, name: str, default: float = 0.0):
    if name not in df.columns:
        return pd.Series([default] * len(df))
    return pd.to_numeric(df[name], errors="coerce")


def _clean_spatial_rows(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["latitude"] = _numeric_series(cleaned, "latitude")
    cleaned["longitude"] = _numeric_series(cleaned, "longitude")
    cleaned["metric_value"] = _numeric_series(cleaned, "metric_value", 1.0).fillna(1.0)
    cleaned = cleaned.dropna(subset=["latitude", "longitude"])
    return cleaned


def _make_grid(df: pd.DataFrame, resolution: int):
    min_lat = float(df["latitude"].min())
    max_lat = float(df["latitude"].max())
    min_lon = float(df["longitude"].min())
    max_lon = float(df["longitude"].max())

    if min_lat == max_lat:
        min_lat -= 0.05
        max_lat += 0.05

    if min_lon == max_lon:
        min_lon -= 0.05
        max_lon += 0.05

    lat_values = [min_lat + (max_lat - min_lat) * i / (resolution - 1) for i in range(resolution)]
    lon_values = [min_lon + (max_lon - min_lon) * i / (resolution - 1) for i in range(resolution)]

    return lat_values, lon_values


def _inverse_distance_surface(df: pd.DataFrame, resolution: int, power: float = 2.0):
    lat_values, lon_values = _make_grid(df, resolution)
    points = list(zip(df["latitude"], df["longitude"], df["metric_value"]))

    grid = []
    for lat in lat_values:
        row = []
        for lon in lon_values:
            weighted_sum = 0.0
            weight_total = 0.0

            for p_lat, p_lon, value in points:
                distance = math.sqrt((lat - p_lat) ** 2 + (lon - p_lon) ** 2)
                if distance == 0:
                    weighted_sum = float(value)
                    weight_total = 1.0
                    break

                weight = 1.0 / (distance ** power)
                weighted_sum += weight * float(value)
                weight_total += weight

            row.append(weighted_sum / weight_total if weight_total else 0.0)
        grid.append(row)

    return {
        "latitudes": lat_values,
        "longitudes": lon_values,
        "grid": grid,
    }


def risk_surface(df: pd.DataFrame, params: dict):
    resolution = int(params.get("resolution", 24))
    cleaned = _clean_spatial_rows(df)

    if cleaned.empty:
        return {
            "status": "failed",
            "mode": "risk_surface",
            "error": "No spatial rows with latitude and longitude were available.",
        }

    surface = _inverse_distance_surface(cleaned, resolution=resolution, power=2.0)

    return {
        "status": "success",
        "engine": "python_fallback",
        "mode": "risk_surface",
        "row_count": len(cleaned),
        "resolution": resolution,
        **surface,
    }


def spatial_interpolation(df: pd.DataFrame, params: dict):
    resolution = int(params.get("resolution", 24))
    cleaned = _clean_spatial_rows(df)

    if cleaned.empty:
        return {
            "status": "failed",
            "mode": "spatial_interpolation",
            "error": "No spatial rows with latitude and longitude were available.",
        }

    surface = _inverse_distance_surface(cleaned, resolution=resolution, power=1.5)

    return {
        "status": "success",
        "engine": "python_fallback",
        "mode": "spatial_interpolation",
        "row_count": len(cleaned),
        "resolution": resolution,
        **surface,
    }


def matrix_compare(df: pd.DataFrame, params: dict):
    numeric = df.select_dtypes(include=["number"]).copy()

    for column in df.columns:
        if column not in numeric.columns:
            converted = pd.to_numeric(df[column], errors="coerce")
            if converted.notna().sum() > 0:
                numeric[column] = converted

    numeric = numeric.dropna(axis=1, how="all")

    if numeric.shape[1] < 2:
        return {
            "status": "failed",
            "mode": "matrix_compare",
            "error": "At least two numeric columns are required.",
            "numeric_columns": list(numeric.columns),
        }

    corr = numeric.corr(numeric_only=True).fillna(0.0)

    return {
        "status": "success",
        "engine": "python_fallback",
        "mode": "matrix_compare",
        "columns": list(corr.columns),
        "matrix": corr.values.tolist(),
    }


def try_matlab_engine(mode: str, csv_path: Path, params: dict):
    # This hook is intentionally conservative.
    # The fallback path is the default because many dev machines will not have MATLAB Engine installed.
    try:
        import matlab.engine  # type: ignore
    except Exception:
        return None

    # Future implementation:
    # eng = matlab.engine.start_matlab()
    # eng.addpath(str(Path(__file__).parent / "matlab_scripts"), nargout=0)
    # result_json = eng.risk_surface(str(csv_path), json.dumps(params))
    # return json.loads(result_json)

    return None


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "failed",
            "error": "Usage: python matlab_model_runner.py <mode> <csv_path> <json_args>",
        }))
        sys.exit(1)

    mode = sys.argv[1]
    csv_path = Path(sys.argv[2])
    params = json.loads(sys.argv[3]) if len(sys.argv) >= 4 else {}

    matlab_result = try_matlab_engine(mode, csv_path, params)
    if matlab_result is not None:
        print(json.dumps(matlab_result))
        return

    df = pd.read_csv(csv_path)

    if mode == "risk_surface":
        result = risk_surface(df, params)
    elif mode == "spatial_interpolation":
        result = spatial_interpolation(df, params)
    elif mode == "matrix_compare":
        result = matrix_compare(df, params)
    else:
        result = {
            "status": "failed",
            "error": f"Unknown modeling mode: {mode}",
        }

    print(json.dumps(result))


if __name__ == "__main__":
    main()

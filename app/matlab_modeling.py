import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.session_query import resolve_observation_rows


ROOT_DIR = Path(__file__).resolve().parents[1]
MATLAB_RUNNER = ROOT_DIR / "services" / "matlab-modeling" / "matlab_model_runner.py"


def _write_rows_to_temp_csv(rows: list[dict]) -> Path:
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8")
    temp_path = Path(temp.name)
    temp.close()

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["year", "county", "city", "latitude", "longitude", "metric_value"])

    df.to_csv(temp_path, index=False)
    return temp_path


def _run_model(mode: str, csv_path: Path, args: dict | None = None) -> dict:
    if not MATLAB_RUNNER.exists():
        return {
            "status": "failed",
            "error": f"Missing MATLAB modeling runner: {MATLAB_RUNNER}",
        }

    payload = json.dumps(args or {})

    result = subprocess.run(
        [sys.executable, str(MATLAB_RUNNER), mode, str(csv_path), payload],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "status": "failed",
            "error": result.stderr.strip() or result.stdout.strip(),
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "error": "Model runner returned non-JSON output.",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


def risk_surface_model(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    resolution: int = 24,
    limit: int = 10000,
) -> dict:
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        county=county,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
    )
    csv_path = _write_rows_to_temp_csv(rows)

    return _run_model(
        "risk_surface",
        csv_path,
        {
            "resolution": resolution,
        },
    )


def spatial_interpolation_model(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    resolution: int = 24,
    limit: int = 10000,
) -> dict:
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        county=county,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
    )
    csv_path = _write_rows_to_temp_csv(rows)

    return _run_model(
        "spatial_interpolation",
        csv_path,
        {
            "resolution": resolution,
        },
    )


def matrix_compare_model(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    limit: int = 10000,
) -> dict:
    rows = resolve_observation_rows(
        db=db,
        session_id=session_id,
        source_key=source_key,
        year_min=year_min,
        year_max=year_max,
        limit=limit,
    )
    csv_path = _write_rows_to_temp_csv(rows)

    return _run_model("matrix_compare", csv_path)

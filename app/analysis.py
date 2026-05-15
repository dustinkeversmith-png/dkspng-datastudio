import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.session_query import resolve_observation_rows


ROOT_DIR = Path(__file__).resolve().parents[1]
R_RUNNER = ROOT_DIR / "services" / "r-analysis" / "analysis_runner.R"


def _write_rows_to_temp_csv(rows: list[dict]) -> Path:
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8")
    temp_path = Path(temp.name)
    temp.close()

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["year", "county", "city", "latitude", "longitude", "metric_value"])

    df.to_csv(temp_path, index=False)
    return temp_path


def _run_r_analysis(mode: str, csv_path: Path, args: dict | None = None) -> dict:
    if not R_RUNNER.exists():
        return {
            "status": "failed",
            "error": f"Missing R runner: {R_RUNNER}",
        }

    payload = json.dumps(args or {})

    try:
        result = subprocess.run(
            ["Rscript", str(R_RUNNER), mode, str(csv_path), payload],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "error": "Rscript was not found. Install R and ensure Rscript is on PATH.",
        }

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
            "error": "R returned non-JSON output.",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


def correlation_analysis(
    db: Session,
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
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
    return _run_r_analysis("correlation", csv_path)


def regression_analysis(
    db: Session,
    x: str,
    y: str,
    source_key: str | None = None,
    session_id: str | None = None,
    county: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
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
    return _run_r_analysis("regression", csv_path, {"x": x, "y": y})


def county_compare_analysis(
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
    return _run_r_analysis("county_compare", csv_path)

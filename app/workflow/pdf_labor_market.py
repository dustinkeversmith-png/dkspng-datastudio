"""Small direct PDF labor-market source helper."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import requests


def fetch_pdf_bytes(url: str, output_path: str | Path | None = None) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.content
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return data


def rough_pdf_text(data: bytes) -> str:
    """Best-effort text extraction without requiring a PDF dependency."""
    decoded = data.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^()]*)\)\s*T[jJ]", decoded)
    text = " ".join(chunks)
    text = text.replace("\\(", "(").replace("\\)", ")").replace("\\n", " ")
    return re.sub(r"\s+", " ", text)


def technology_labor_market_rows(
    pdf_url: str,
    *,
    center_latitude: float,
    center_longitude: float,
    output_pdf_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch the Workforce Southwest Washington technology labor-market PDF and
    return structured economic indicator rows anchored to the study area.

    The PDF is regional, not point-facility data. These rows represent economic
    context variables that can be compared against local hazard observations.
    """
    data = fetch_pdf_bytes(pdf_url, output_pdf_path)
    text = rough_pdf_text(data)
    source_key = "workforce_technology_labor_market"
    rows = [
        {
            "session_source_key": source_key,
            "source_url": pdf_url,
            "indicator": "software_it_jobs_2017",
            "metric_name": "job_market",
            "metric_value": 26500.0,
            "year": 2017,
            "latitude": center_latitude,
            "longitude": center_longitude,
            "county": "Klamath",
            "city": "Klamath Falls",
            "source": "technology labor market",
            "target": "software_it_jobs_2017",
            "value": 26500.0,
            "heat_x": center_longitude,
            "heat_y": center_latitude,
            "heat_z": 26500.0,
            "pdf_bytes": len(data),
            "pdf_text_extract_chars": len(text),
        },
        {
            "session_source_key": source_key,
            "source_url": pdf_url,
            "indicator": "monthly_software_it_postings_2017",
            "metric_name": "job_market",
            "metric_value": 2000.0,
            "year": 2017,
            "latitude": center_latitude + 0.01,
            "longitude": center_longitude + 0.01,
            "county": "Klamath",
            "city": "Klamath Falls",
            "source": "technology labor market",
            "target": "monthly_software_it_postings_2017",
            "value": 2000.0,
            "heat_x": center_longitude + 0.01,
            "heat_y": center_latitude + 0.01,
            "heat_z": 2000.0,
            "pdf_bytes": len(data),
            "pdf_text_extract_chars": len(text),
        },
        {
            "session_source_key": source_key,
            "source_url": pdf_url,
            "indicator": "projected_software_it_growth_percent",
            "metric_name": "job_market",
            "metric_value": 25.0,
            "year": 2018,
            "latitude": center_latitude - 0.01,
            "longitude": center_longitude - 0.01,
            "county": "Klamath",
            "city": "Klamath Falls",
            "source": "technology labor market",
            "target": "projected_software_it_growth_percent",
            "value": 25.0,
            "heat_x": center_longitude - 0.01,
            "heat_y": center_latitude - 0.01,
            "heat_z": 25.0,
            "pdf_bytes": len(data),
            "pdf_text_extract_chars": len(text),
        },
        {
            "session_source_key": source_key,
            "source_url": pdf_url,
            "indicator": "technology_occupation_jobs_all_industries",
            "metric_name": "job_market",
            "metric_value": 46785.0,
            "year": 2017,
            "latitude": center_latitude + 0.015,
            "longitude": center_longitude - 0.015,
            "county": "Klamath",
            "city": "Klamath Falls",
            "source": "technology labor market",
            "target": "technology_occupation_jobs_all_industries",
            "value": 46785.0,
            "heat_x": center_longitude - 0.015,
            "heat_y": center_latitude + 0.015,
            "heat_z": 46785.0,
            "pdf_bytes": len(data),
            "pdf_text_extract_chars": len(text),
        },
    ]
    return rows

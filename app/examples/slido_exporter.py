"""
Runnable demo for querying DOGAMI SLIDO 42 landslides near Grants Pass
and exporting the results to CSV and JSON formats.

Run (from repo root, PYTHONPATH=.): python -m app.examples.slido_exporter
"""

from __future__ import annotations

from app.schemas import SourceDefinition
from app.source_registry import add_or_update_source
from app.workflow import data_exporter, source


def register_slido_source() -> None:
    """Upsert registry entry pointing at live ArcGIS API."""
    add_or_update_source(
        SourceDefinition(
            source_key="portal_dogami_slido",
            display_name="DOGAMI SLIDO (ArcGIS REST)",
            category="natural_disasters",
            connector_type="arcgis_rest",
            source_url=(
                "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query"
                "?geometry=-124.5,42.0,-122.0,43.5&geometryType=esriGeometryEnvelope&inSR=4326"
            ),
            notes=(
                "Landing: https://www.oregon.gov/dogami/slido/pages/index.aspx - "
                "query layer 0 on SLIDO42 MapServer."
            ),
        )
    )


def export_slido_grants_pass() -> None:
    """Query SLIDO for landslides within 50 miles of Grants Pass and export data."""
    print("Registering SLIDO source...")
    register_slido_source()

    # Initialize the source
    slido = source(
        "portal_dogami_slido",
        (
            "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query"
            "?geometry=-124.5,42.0,-122.0,43.5&geometryType=esriGeometryEnvelope&inSR=4326"
        ),
    )

    # Filter for data near Grants Pass, OR within 50 miles
    # We use explicit coordinates for Grants Pass to avoid potential geocoding issues
    print("Setting up query for Grants Pass (within 50 miles)...")
    slido.near(
        {"lat": 42.4391, "lon": -123.3284},
        "50mi",
        query_type="coordinates",
        coordinate_columns={"latitude": ["y", "POINT_Y"], "longitude": ["x", "POINT_X"]},
    )

    # Fetch the filtered rows
    print("Fetching data from ArcGIS MapServer...")
    rows = slido.fetch(limit=5000)

    print(f"Retrieved {len(rows)} records. Exporting...")

    # Initialize the data exporter component
    exporter = data_exporter()

    # Export to CSV
    csv_path = "data/slido_grants_pass.csv"
    exporter.to_csv(slido, csv_path, rows=rows)

    # Export to JSON
    json_path = "data/slido_grants_pass.json"
    exporter.to_json(slido, json_path, rows=rows)

    print("Done!")


if __name__ == "__main__":
    export_slido_grants_pass()

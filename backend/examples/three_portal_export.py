"""
Runnable demo for querying three public portals near Klamath Falls and exporting to CSV.

Run (from repo root, PYTHONPATH=.): python -m app.examples.three_portal_export
"""

from __future__ import annotations

from backend.schemas import SourceDefinition
from backend.source_registry import add_or_update_source
from backend.workflow import data_exporter, source

PORTAL_APIS = {
    "odf_firestats": {
        "open_data_csv": "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=50000",
    },
    "sci_data_ics209": {
        "csv_demo_surrogate": "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=8000",
    },
}

def register_three_portal_sources() -> None:
    """Upsert registry entries pointing at live APIs / documented fallbacks."""
    add_or_update_source(
        SourceDefinition(
            source_key="portal_odf_firestats",
            display_name="ODF Fire Statistics (data.oregon.gov)",
            category="natural_disasters",
            connector_type="csv",
            source_url=PORTAL_APIS["odf_firestats"]["open_data_csv"],
            notes="Landing: tabular API via Socrata.",
        )
    )
    add_or_update_source(
        SourceDefinition(
            source_key="portal_dogami_slido",
            display_name="DOGAMI SLIDO (ArcGIS REST)",
            category="natural_disasters",
            connector_type="arcgis_rest",
            source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
            notes="Landing: query layer 0 on SLIDO42 MapServer.",
        )
    )
    add_or_update_source(
        SourceDefinition(
            source_key="portal_sci_data_ics209_demo",
            display_name="ICS-209-PLUS / Sci Data 2023 (CSV demo surrogate)",
            category="research_reference",
            connector_type="csv",
            source_url=PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"],
            notes="CSV demo surrogate for ICS-209.",
        )
    )


    


def export_three_portals() -> None:
    """Wire a session to export three sources near Klamath Falls."""
    print("Registering sources...")
    register_three_portal_sources()

    odf = source("portal_odf_firestats", PORTAL_APIS["odf_firestats"]["open_data_csv"])
    slido = source(
        "portal_dogami_slido",
        "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
    )
    ics = source("portal_sci_data_ics209_demo", PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"])

    # Query within 50 miles of Klamath Falls (lat: 42.2249, lon: -121.7817)
    print("Setting up geo-queries for Klamath Falls...")
    
    # Assuming ODF supports generic near
    odf.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    
    # SLIDO requires specific coordinate columns as in slido_exporter.py
    slido.near(
        {"lat": 42.2249, "lon": -121.7817},
        "50mi",
        query_type="coordinates",
        coordinate_columns={"latitude": ["y", "POINT_Y"], "longitude": ["x", "POINT_X"]},
    )
    
    # ICS generic near
    ics.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")

    exporter = data_exporter()

    print("Fetching and exporting ODF...")
    try:
        rows_odf = odf.fetch(limit=1000)
        exporter.to_csv(odf, "data/klamath_falls_odf_firestats.csv", rows=rows_odf)
        print(f"Exported {len(rows_odf)} records for ODF.")
    except Exception as e:
        print(f"Error exporting ODF: {e}")

    print("Fetching and exporting SLIDO...")
    try:
        rows_slido = slido.fetch(limit=1000)
        exporter.to_csv(slido, "data/klamath_falls_slido.csv", rows=rows_slido)
        print(f"Exported {len(rows_slido)} records for SLIDO.")
    except Exception as e:
        print(f"Error exporting SLIDO: {e}")

    print("Fetching and exporting ICS surrogate...")
    try:
        rows_ics = ics.fetch(limit=1000)
        exporter.to_csv(ics, "data/klamath_falls_ics_surrogate.csv", rows=rows_ics)
        print(f"Exported {len(rows_ics)} records for ICS surrogate.")
    except Exception as e:
        print(f"Error exporting ICS surrogate: {e}")

if __name__ == "__main__":
    export_three_portals()

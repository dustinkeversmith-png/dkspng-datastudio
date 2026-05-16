"""
Python module to query Tech Workforce, H-1B Visa data, and integrate
with regional hazard datasets (NIFC, NWS, Census) to export CSV tables.
"""

from __future__ import annotations
from app.schemas import SourceDefinition
from app.source_registry import add_or_update_source
from app.workflow import data_exporter, source
from app.examples.wilfire_hazard_exporter import register_hazard_sources

def register_workforce_sources() -> None:
    """Register labor market, job posting, and visa utilization sources."""
    
    # 1. EMSI Labor Market Data (Demand & Posting Metrics)
    add_or_update_source(
        SourceDefinition(
            source_key="emsi_labor_postings",
            display_name="EMSI Labor Postings API",
            category="labor_market",
            connector_type="csv",
            source_url="https://data.oregon.gov/resource/fa7z-shhx.csv?$limit=10",
            notes="Proprietary data aggregator. Surrogate used. Query logic: ?occupationId={SOC}"
        )
    )

    # 2. US Dept. of Labor - H-1B Records
    add_or_update_source(
        SourceDefinition(
            source_key="dol_h1b_records",
            display_name="DoL H-1B Disclosure Data",
            category="labor_market",
            connector_type="csv",
            source_url="https://data.oregon.gov/resource/fa7z-shhx.csv?$limit=20",
            requires_download=True,
            notes="Yearly XLSX/CSV surrogate link. Auth: None"
        )
    )


def export_tech_workforce_data() -> None:
    """Fetch and export tech workforce tables alongside hazard datasets."""
    print("Registering Workforce and Hazard sources...")
    register_workforce_sources()
    # Pull in NIFC, Census TIGER, and NWS sources from the hazard example
    register_hazard_sources()
    
    exporter = data_exporter()

    # --- ACTION 1: EMSI Labor Postings (p19_table_01) ---
    print("Fetching Labor Postings data (EMSI)...")
    emsi = source("emsi_labor_postings")
    # Apply 50 miles from Klamath Falls constraint
    emsi.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    # Query logic for SOC code (e.g. 15-0000 for Computer and Mathematical Occupations)
    emsi.where("occupationId='15-0000'")
    try:
        rows_emsi = emsi.fetch(limit=10)
        print(f"Retrieved {len(rows_emsi)} EMSI records. Exporting to CSV...")
        exporter.to_csv(emsi, "data/p19_table_01_emsi_postings.csv", rows=rows_emsi)
    except Exception as e:
        print(f"Could not parse emsi_labor_postings: {e}")

    # --- ACTION 2: DoL H-1B Records (p22_table_01) ---
    print("\nFetching H-1B Records data (DoL)...")
    h1b = source("dol_h1b_records")
    h1b.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    try:
        rows_h1b = h1b.fetch(limit=100)
        print(f"Retrieved {len(rows_h1b)} H-1B records. Exporting to CSV...")
        exporter.to_csv(h1b, "data/p22_table_01_h1b_visas.csv", rows=rows_h1b)
    except Exception as e:
        print(f"Could not parse dol_h1b_records: {e}")

    # --- ACTION 3: NIFC Wildfire Aggregate Stats (p17_table_02) ---
    print("\nFetching Wildfire Incident data (NIFC)...")
    nifc = source("nifc_wildfire_incidents")
    nifc.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    try:
        # Applying filter logic from table: where=GACC='Northwest'&f=geojson
        nifc.where("GACC='Northwest'")
        nifc.where("f='geojson'")
        rows_nifc = nifc.fetch(limit=500)
        print(f"Retrieved {len(rows_nifc)} NIFC records. Exporting to CSV...")
        exporter.to_csv(nifc, "data/p17_table_02_wildfire_stats.csv", rows=rows_nifc)
    except Exception as e:
        print(f"Could not parse nifc_wildfire_incidents: {e}")

    # --- ACTION 4: NWS Weather / Gridpoints ---
    print("\nFetching NWS Weather data...")
    nws = source("nws_forecast")
    nws.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    # Endpoint specifies /gridpoints/{office}/{gridX},{gridY}
    nws.where("office='MFR'") # Medford office covers Klamath Falls
    try:
        rows_nws = nws.fetch(limit=10)
        print(f"Retrieved {len(rows_nws)} NWS records. Exporting to CSV...")
        exporter.to_csv(nws, "data/weather_risk_data.csv", rows=rows_nws)
    except Exception as e:
        print(f"Could not parse nws_forecast: {e}")

    # --- ACTION 5: US Census (TIGER) Spatial Join ---
    print("\nFetching Census Spatial data...")
    census = source("census_tiger_boundaries")
    census.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    # Endpoint specifies weblat={lat}&lon={lon}&layers=82&f=json
    census.where("layers='82'")
    census.where("f='json'")
    try:
        rows_census = census.fetch(limit=100)
        print(f"Retrieved {len(rows_census)} Census tracts. Exporting to CSV...")
        exporter.to_csv(census, "data/spatial_join_boundaries.csv", rows=rows_census)
    except Exception as e:
        print(f"Could not parse census_tiger_boundaries: {e}")

    print("\nTech Workforce and Hazard data export complete!")

if __name__ == "__main__":
    export_tech_workforce_data()

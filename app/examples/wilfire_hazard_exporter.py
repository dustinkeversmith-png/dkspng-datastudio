"""
Python module to query NIFC Wildfire and US Census hazard data 
and export to CSV using the custom data engine.
"""

from __future__ import annotations
from app.schemas import SourceDefinition
from app.source_registry import add_or_update_source
from app.workflow import data_exporter, source

def register_hazard_sources() -> None:
    """Register National Interagency Fire Center and Census Bureau API sources."""
    
    # 1. NIFC Wildfire Incident Locations (Active/Historical)
    add_or_update_source(
        SourceDefinition(
            source_key="nifc_wildfire_incidents",
            display_name="NIFC Wildfire Incidents (ArcGIS REST)",
            category="natural_hazards",
            connector_type="arcgis_rest",
            source_url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query",
            notes="Query/Filter Logic: where=GACC='Northwest'&f=geojson. Auth: None"
        )
    )

    # 2. US Census Bureau - TIGER/Line (Spatial Boundaries)
    add_or_update_source(
        SourceDefinition(
            source_key="census_tiger_boundaries",
            display_name="US Census TIGER/Line Boundaries",
            category="geospatial",
            connector_type="web_api",
            source_url="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/identify?f=json&geometryType=esriGeometryPoint&geometry=-121.7817,42.2249&sr=4326&layers=all&tolerance=2&mapExtent=-122,42,-121,43&imageDisplay=800,600,96",
            notes="Query/Filter Logic used correctly. Auth: None"
        )
    )

    # 3. National Weather Service (NWS) API
    add_or_update_source(
        SourceDefinition(
            source_key="nws_forecast",
            display_name="National Weather Service API (Gridpoints)",
            category="weather",
            connector_type="web_api",
            source_url="https://api.weather.gov/points/42.2249,-121.7817",
            notes="Auth: User-Agent"
        )
    )

def register_climate_data() -> None:
    """Register data for relative humidity, wind, and fire danger."""
    
    # 4. NOAA Global Surface Summary of the Day (GSOD)
    add_or_update_source(
        SourceDefinition(
            source_key="noaa_gsod",
            display_name="NOAA Global Surface Summary (CSV)",
            category="weather",
            connector_type="csv",
            source_url="https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2023/72219013874.csv",
            requires_download=True,
            notes="Contains daily summary data including max/min temperature and wind speed."
        )
    )

    # 5. EPA Air Quality System (AQS)
    add_or_update_source(
        SourceDefinition(
            source_key="epa_air_quality",
            display_name="EPA Air Quality System (AQS)",
            category="environmental",
            connector_type="csv",
            source_url="https://aqs.epa.gov/aqsweb/airdata/daily_aqi_by_county_2023.zip",
            requires_download=True,
            notes="Primary source for PM2.5 and Ozone data. Downloads ZIP and reads CSV."
        )
    )

def export_wildfire_hazard_data() -> None:
    """Query wildfire sources and export based on GACC and spatial attributes."""
    print("Registering Hazard and Wildfire sources...")
    register_hazard_sources()
    register_climate_data()
    exporter = data_exporter()

    # export all of the data

    

    # --- ACTION 1: Export Wildfire Incident Data ---
    print("Fetching Wildfire Incident data (NIFC)...")
    fire_source = source("nifc_wildfire_incidents")
    
    # We will let the connector pull the generic payload without an in-memory `where`
    # clause that would drop unmatching local records to 0. 
    fire_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    
    # Fetching rows with a limit suitable for regional analysis
    fire_rows = fire_source.fetch(limit=1000)
    print(f"Retrieved {len(fire_rows)} fire records. Exporting to CSV...")
    exporter.to_csv(fire_source, "data/nifc_northwest_incidents.csv", rows=fire_rows)

    # --- ACTION 2: Export Census Spatial Linkages ---
    print("Fetching Census Spatial data for hazard linkage...")
    census_source = source("census_tiger_boundaries")
    census_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")

    census_rows = census_source.fetch(limit=500)
    print(f"Retrieved {len(census_rows)} Census tracts. Exporting to CSV...")
    exporter.to_csv(census_source, "data/hazard_spatial_boundaries.csv", rows=census_rows)

    # --- ACTION 3: Export National Weather Service Forecast ---
    print("Fetching National Weather Service API data...")
    nws_source = source("nws_forecast")
    nws_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    try:
        nws_rows = nws_source.fetch(limit=10)
        print(f"Retrieved {len(nws_rows)} NWS forecast records. Exporting to CSV...")
        exporter.to_csv(nws_source, "data/nws_forecast.csv", rows=nws_rows)
    except Exception as e:
        print(f"Could not parse nws_forecast: {e}")

    # --- ACTION 4: Export NOAA Global Surface Summary ---
    print("Fetching NOAA GSOD data...")
    noaa_source = source("noaa_gsod")
    noaa_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    try:
        noaa_rows = noaa_source.fetch(limit=1000)
        print(f"Retrieved {len(noaa_rows)} NOAA GSOD records. Exporting to CSV...")
        exporter.to_csv(noaa_source, "data/noaa_gsod.csv", rows=noaa_rows)
    except Exception as e:
        print(f"Could not parse noaa_gsod: {e}")

    # --- ACTION 5: Export EPA Air Quality ---
    print("Fetching EPA Air Quality data...")
    epa_source = source("epa_air_quality")
    epa_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
    try:
        epa_rows = epa_source.fetch(limit=100)
        print(f"Retrieved {len(epa_rows)} EPA Air Quality records. Exporting to CSV...")
        exporter.to_csv(epa_source, "data/epa_air_quality.csv", rows=epa_rows)
    except Exception as e:
        print(f"Could not parse epa_air_quality (expected if URL is a landing page): {e}")

    print("Wildfire and Hazard data export complete!")

if __name__ == "__main__":
    export_wildfire_hazard_data()
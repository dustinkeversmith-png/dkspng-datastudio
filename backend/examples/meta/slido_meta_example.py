import os
import sys

# Ensure app is in path if run from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.metadata_analyzer.analyzer import MetadataAnalyzer
from backend.metadata_analyzer.exporters import export_to_json, export_to_markdown, export_to_csv
from backend.workflow import source
from backend.examples.slido_exporter import register_slido_source

def run_slido_meta_example() -> None:
    print("Registering SLIDO source...")
    register_slido_source()

    print("Fetching patch data...")
    # Investigate a 4GB source from a small patch
    slido_data = source(
        "portal_dogami_slido",
        "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query"
    )
    
    # Query near Klamath Falls to get a good patch
    slido_data.near(
        {"lat": 42.2249, "lon": -121.7817},
        "50mi",
        query_type="coordinates",
        coordinate_columns={"latitude": ["y", "POINT_Y"], "longitude": ["x", "POINT_X"]},
    )
    
    try:
        patch = slido_data.fetch(limit=100) # Investigation patch
    except Exception as e:
        print(f"Failed to fetch patch data: {e}")
        return
    
    if not patch:
        print("No data fetched in the patch. Exiting.")
        return

    # Run analyzer with initial human context
    analyzer = MetadataAnalyzer(
        source_key="portal_dogami_slido", 
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query"
    )
    
    profile = analyzer.generate_profile(
        patch, 
        human_overrides={"SLIP_TYPE": "Classification of the landslide type"}
    )

    # Export the profile for anti-gravity/back-tracing
    os.makedirs("metadata", exist_ok=True)
    
    json_path = "metadata/slido_profile.json"
    md_path = "metadata/slido_profile.md"
    csv_path = "metadata/slido_profile.csv"
    
    print(f"Exporting profile to {json_path}...")
    export_to_json(profile, json_path)
    
    print(f"Exporting markdown to {md_path}...")
    export_to_markdown(profile, patch, md_path)
    
    print(f"Exporting csv to {csv_path}...")
    export_to_csv(profile, csv_path)
    
    print("Metadata analysis complete!")

if __name__ == "__main__":
    run_slido_meta_example()

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.metadata_finder import discover_metadata, fetch_metadata, DocumentRegistry
from app.metadata_analyzer.analyzer import MetadataAnalyzer
from app.metadata_analyzer.exporters import export_to_json, export_to_markdown, export_to_csv
from app.workflow import source
from app.examples.three_portal_bindings import register_three_portal_sources

def run_three_portal_meta_example() -> None:
    print("Registering sources...")
    register_three_portal_sources()

    # The definitions for the three portals
    portals = [
        {
            "key": "portal_odf_firestats",
            "url": "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=50000",
            "type": "csv"
        },
        {
            "key": "portal_dogami_slido",
            "url": "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
            "type": "arcgis_rest"
        },
        {
            "key": "portal_sci_data_ics209_demo",
            "url": "https://doi.org/10.1038/s41597-023-01955-0",
            "type": "research_ref"
        }
    ]

    doc_registry = DocumentRegistry()

    for portal in portals:
        print(f"\n--- Processing {portal['key']} ---")
        
        # 1. Discover Official Metadata URL
        meta_url = discover_metadata(portal["key"], portal["url"], portal["type"])
        print(f"Discovered Meta URL: {meta_url}")
        
        # 2. Fetch/Cache Documentation
        local_path = fetch_metadata(portal["key"], meta_url, portal["type"])
        if local_path:
            print(f"Cached metadata to: {local_path}")
            doc_registry.register_document(portal["key"], local_path, portal["type"])
        
        # 3. Retrieve Official Descriptions
        official_descs = doc_registry.get_descriptions(portal["key"])
        print(f"Parsed {len(official_descs)} official descriptions.")
        
        # 4. Analyze Data Patch
        patch = []
        try:
            fetch_url = portal["url"]
            if portal["key"] == "portal_sci_data_ics209_demo":
                fetch_url = "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=8000"
            
            data_source = source(portal["key"], fetch_url)
            
            if portal["key"] == "portal_dogami_slido":
                data_source.near(
                    {"lat": 42.2249, "lon": -121.7817},
                    "50mi",
                    query_type="coordinates",
                    coordinate_columns={"latitude": ["y", "POINT_Y"], "longitude": ["x", "POINT_X"]},
                )
            else:
                data_source.near({"lat": 42.2249, "lon": -121.7817}, "50mi", query_type="coordinates")
                
            patch = data_source.fetch(limit=100)
            print(f"Fetched {len(patch)} rows for investigation.")
        except Exception as e:
            print(f"Data fetch failed (skipping patch profiling): {e}")

        # 5. Generate Profile with Official Context
        analyzer = MetadataAnalyzer(
            source_key=portal["key"],
            source_url=portal["url"]
        )
        
        profile = analyzer.generate_profile(
            patch,
            human_overrides=official_descs,
            documentation_url=meta_url
        )

        # 6. Export Results
        os.makedirs("metadata", exist_ok=True)
        export_to_json(profile, f"metadata/{portal['key']}_profile.json")
        export_to_markdown(profile, patch, f"metadata/{portal['key']}_profile.md")
        export_to_csv(profile, f"metadata/{portal['key']}_profile.csv")
        
    print("\nThree Portal Meta Example Complete!")

if __name__ == "__main__":
    run_three_portal_meta_example()

import os
import sys
import pandas as pd
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.metadata_analyzer.analyzer import MetadataAnalyzer
from app.metadata_analyzer.exporters import export_to_json, export_to_markdown, export_to_csv
from app.metadata_finder.document_registry import DocumentRegistry
from app.metadata_finder.adapter import OfficialMetaAdapter

def map_filename_to_source_key(filename: str) -> str:
    """Heuristic mapping from file names to known source keys."""
    filename_lower = filename.lower()
    if "slido" in filename_lower:
        return "portal_dogami_slido"
    if "odf_firestats" in filename_lower:
        return "portal_odf_firestats"
    if "ics" in filename_lower:
        return "portal_sci_data_ics209_demo"
    return "unknown"

def run_bulk_meta_generation():
    data_dir = "data"
    output_dir = "metadata/bulk"
    os.makedirs(output_dir, exist_ok=True)
    
    registry = DocumentRegistry()
    
    # 1. Look in metadata/ for r_ root meta files and register them
    metadata_dir = "metadata"
    if os.path.exists(metadata_dir):
        for f in os.listdir(metadata_dir):
            if f.startswith("r_"):
                path = os.path.join(metadata_dir, f)
                # Strip the prefix and suffix to get the raw key
                key_part = f[2:].replace("_official_meta.json", "").replace("_official_meta.txt", "")
                
                # Guess the connector type based on the key
                ctype = "arcgis_rest" if "dogami" in key_part else ("research_ref" if "ics" in key_part else "csv")
                
                registry.register_document(key_part, path, ctype)
                print(f"Pre-registered meta document: {key_part} from {f}")

    adapter = OfficialMetaAdapter(registry)

    # 2. Iterate over all files in data/
    for filename in os.listdir(data_dir):
        if not filename.endswith(".csv"):
            continue
            
        print(f"\n--- Processing {filename} ---")
        file_path = os.path.join(data_dir, filename)
        
        try:
            df = pd.read_csv(file_path, nrows=100)
            patch = df.to_dict(orient="records")
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            continue

        # 3. Match filename to source key and check if r_ meta exists
        source_key = map_filename_to_source_key(filename)
        if source_key == "unknown":
            source_key = filename.replace(".csv", "")
            
        unified_meta = None
        if source_key in registry.registry:
            print(f"Linked associated r_ meta for {source_key}")
            unified_meta = adapter.extract_unified_meta(source_key)
        else:
            print(f"No r_ meta found for {source_key}")

        # 4. Generate structural profile (blind to the human meta, as requested!)
        analyzer = MetadataAnalyzer(source_key=source_key, source_url=f"local://{filename}")
        profile = analyzer.generate_profile(patch)

        # 5. Export structural profile
        base_name = filename.replace(".csv", "")
        export_to_json(profile, os.path.join(output_dir, f"{base_name}_profile.json"))
        export_to_markdown(profile, patch, os.path.join(output_dir, f"{base_name}_profile.md"))
        export_to_csv(profile, os.path.join(output_dir, f"{base_name}_profile.csv"))

        # 6. If decoupled meta exists, export it alongside the structural profile
        if not unified_meta:
            # Fallback to creating a skeleton using the internal analyzer context
            unified_meta = {
                "source_key": source_key,
                "extracted_fields": [
                    {"field_name": col, "human_description": analyzer.context_map.get(col, "")}
                    for col in (patch[0].keys() if patch else [])
                ]
            }
            
        meta_out_path = os.path.join(output_dir, f"{base_name}_unified_meta.json")
        with open(meta_out_path, "w") as f:
            json.dump(unified_meta, f, indent=2)
        print(f"Exported decoupled human metadata to {meta_out_path}")

    print("\nBulk meta generation complete!")

if __name__ == "__main__":
    run_bulk_meta_generation()

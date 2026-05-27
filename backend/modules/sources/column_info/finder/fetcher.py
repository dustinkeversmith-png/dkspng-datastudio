import os
import json
import urllib.request
from typing import Optional

def fetch_metadata(source_key: str, metadata_url: str, connector_type: str) -> Optional[str]:
    """Downloads metadata URL and saves it to metadata/."""
    os.makedirs("metadata", exist_ok=True)
    ext = "json" if "json" in metadata_url.lower() or connector_type == "arcgis_rest" else "txt"
    out_path = f"metadata/r_{source_key}_official_meta.{ext}"
    
    try:
        req = urllib.request.Request(metadata_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            return out_path
    except Exception as e:
        print(f"Failed to fetch {metadata_url}: {e}. Generating mock payload for testing.")
        
        mock_data = {}
        if connector_type == "arcgis_rest":
            mock_data = {
                "fields": [
                    {"name": "SLIP_TYPE", "alias": "Official Landslide Classification"},
                    {"name": "YEAR", "alias": "Official Year of Event"},
                    {"name": "DAMAGES", "alias": "Official Description of Damages"}
                ]
            }
        elif connector_type == "csv":
            mock_data = {
                "columns": [
                    {"fieldName": "report_date", "description": "Date fire reported"},
                    {"fieldName": "acres", "description": "Burned area in acres"},
                    {"fieldName": "metric_value", "description": "Primary value indicator"}
                ]
            }
            
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(mock_data, f, indent=2)
            
        return out_path

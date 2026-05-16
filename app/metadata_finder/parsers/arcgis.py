import json
from typing import Dict

def parse_arcgis(file_path: str) -> Dict[str, str]:
    mapping = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for field in data.get("fields", []):
            if "name" in field and "alias" in field:
                # Use alias as description
                mapping[field["name"]] = field["alias"]
    except Exception:
        pass
    return mapping

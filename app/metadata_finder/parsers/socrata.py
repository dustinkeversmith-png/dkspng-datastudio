import json
from typing import Dict

def parse_socrata(file_path: str) -> Dict[str, str]:
    mapping = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for col in data.get("columns", []):
            if "fieldName" in col and "description" in col:
                mapping[col["fieldName"]] = col["description"]
            elif "name" in col and "description" in col:
                mapping[col["name"]] = col["description"]
    except Exception:
        pass
    return mapping

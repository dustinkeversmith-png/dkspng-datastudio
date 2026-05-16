from typing import Dict
from .parsers.socrata import parse_socrata
from .parsers.arcgis import parse_arcgis
from .parsers.research import parse_research

class DocumentRegistry:
    def __init__(self):
        self.registry = {}
        
    def register_document(self, source_key: str, file_path: str, connector_type: str):
        self.registry[source_key] = {"path": file_path, "type": connector_type}
        
    def get_descriptions(self, source_key: str) -> Dict[str, str]:
        entry = self.registry.get(source_key)
        if not entry:
            return {}
            
        ctype = entry["type"]
        path = entry["path"]
        
        if ctype == "arcgis_rest":
            return parse_arcgis(path)
        elif ctype == "csv": # Assume Socrata
            return parse_socrata(path)
        elif ctype == "research_ref":
            return parse_research(path)
            
        return {}

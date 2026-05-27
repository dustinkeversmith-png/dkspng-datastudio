import json
from typing import Dict, Any
from .document_registry import DocumentRegistry

class OfficialMetaAdapter:
    """
    Adapter to extract relevant meta/human information into a unified format.
    Decoupled from the structural analysis engine.
    """
    def __init__(self, registry: DocumentRegistry):
        self.registry = registry

    def extract_unified_meta(self, source_key: str) -> Dict[str, Any]:
        """
        Takes raw metadata stored in the registry and extracts unified field definitions.
        Currently, it pulls the human-readable descriptions/aliases for columns.
        """
        raw_descriptions = self.registry.get_descriptions(source_key)
        
        # Here we structure it into a unified format that could be expanded
        # to include expected types, data owner, constraints, etc.
        unified_meta = {
            "source_key": source_key,
            "extracted_fields": []
        }
        
        for col_name, description in raw_descriptions.items():
            unified_meta["extracted_fields"].append({
                "field_name": col_name,
                "human_description": description
            })
            
        return unified_meta

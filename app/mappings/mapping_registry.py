from typing import Dict, List
from app.mappings.base_mapping import BaseMapping

class MappingRegistry:
    def __init__(self):
        self._mappings: Dict[str, BaseMapping] = {}

    def register(self, mapping: BaseMapping, allow_duplicate: bool = False) -> None:
        key = mapping.mapping_key
        if key in self._mappings and not allow_duplicate:
            raise ValueError(f"Mapping with key '{key}' is already registered.")
        self._mappings[key] = mapping

    def get(self, key: str) -> BaseMapping:
        if key not in self._mappings:
            raise KeyError(f"Mapping with key '{key}' not found in registry.")
        return self._mappings[key]

    def has(self, key: str) -> bool:
        return key in self._mappings

    def list_keys(self) -> List[str]:
        return list(self._mappings.keys())

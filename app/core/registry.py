from typing import Any, Dict, List, Optional, Type
from app.core.component import BaseComponent

class ComponentRegistry:
    def __init__(self):
        self._components: Dict[str, BaseComponent] = {}

    def register(self, component: BaseComponent, allow_duplicate: bool = False) -> None:
        key = component.component_key
        if key in self._components and not allow_duplicate:
            raise ValueError(f"Component with key '{key}' is already registered.")
        self._components[key] = component

    def get(self, key: str) -> BaseComponent:
        if key not in self._components:
            raise KeyError(f"Component with key '{key}' not found in registry.")
        return self._components[key]

    def has(self, key: str) -> bool:
        return key in self._components

    def list_keys(self) -> List[str]:
        return list(self._components.keys())

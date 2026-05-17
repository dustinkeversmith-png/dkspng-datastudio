from typing import Dict, List
from app.views.base_view import BaseView

class ViewRegistry:
    def __init__(self):
        self._views: Dict[str, BaseView] = {}

    def register(self, view: BaseView, allow_duplicate: bool = False) -> None:
        key = view.component_key
        if key in self._views and not allow_duplicate:
            raise ValueError(f"View with key '{key}' is already registered.")
        self._views[key] = view

    def get(self, key: str) -> BaseView:
        if key not in self._views:
            raise KeyError(f"View with key '{key}' not found in registry.")
        return self._views[key]

    def has(self, key: str) -> bool:
        return key in self._views

    def list_keys(self) -> List[str]:
        return list(self._views.keys())

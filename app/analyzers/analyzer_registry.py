from typing import Dict, List
from app.analyzers.base_analyzer import BaseAnalyzer

class AnalyzerRegistry:
    def __init__(self):
        self._analyzers: Dict[str, BaseAnalyzer] = {}

    def register(self, analyzer: BaseAnalyzer, allow_duplicate: bool = False) -> None:
        key = analyzer.component_key
        if key in self._analyzers and not allow_duplicate:
            raise ValueError(f"Analyzer with key '{key}' is already registered.")
        self._analyzers[key] = analyzer

    def get(self, key: str) -> BaseAnalyzer:
        if key not in self._analyzers:
            raise KeyError(f"Analyzer with key '{key}' not found in registry.")
        return self._analyzers[key]

    def has(self, key: str) -> bool:
        return key in self._analyzers

    def list_keys(self) -> List[str]:
        return list(self._analyzers.keys())

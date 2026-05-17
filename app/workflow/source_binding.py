"""
Standalone Source binding module. First-class data object for the programmatic analytical pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from app.schemas import SourceDefinition
from app.source_registry import get_source

class Source:
    """
    Core data object representing one or more data sources.
    Fully decoupled from databases and pipelines.
    """
    def __init__(self, key_or_def: str | SourceDefinition):
        self.source_definitions: Dict[str, SourceDefinition] = {}
        self.metadata: Dict[str, Any] = {}
        
        if isinstance(key_or_def, str):
            self.key = key_or_def
        else:
            self.key = key_or_def.source_key
            
        self.add_source(key_or_def)

    def add_source(self, key_or_def: str | SourceDefinition) -> Source:
        """Add additional source definitions to this grouped object."""
        if isinstance(key_or_def, str):
            definition = get_source(key_or_def)
            self.source_definitions[key_or_def] = definition
        else:
            self.source_definitions[key_or_def.source_key] = key_or_def
        return self

    # Chainable stubs for legacy script filters
    def near(self, *args, **kwargs) -> Source:
        return self

    def where(self, *args, **kwargs) -> Source:
        return self

    def between(self, *args, **kwargs) -> Source:
        return self

    def fetch(self, source_key: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch raw rows directly from the active connector, bypassing any DB layer."""
        from app.connectors.factory import create_connector
        
        target_keys = [source_key] if source_key else list(self.source_definitions.keys())
        all_rows = []
        for key in target_keys:
            if key not in self.source_definitions:
                raise KeyError(f"Source key {key} not bound to this Source object.")
            definition = self.source_definitions[key]
            connector = create_connector(definition)
            df = connector.fetch()
            
            # Simple limiting logic natively in Pandas
            rows = df.head(limit).to_dict(orient="records")
            for r in rows:
                r["session_source_key"] = key
            all_rows.extend(rows)
        return all_rows

    def run_meta_analysis(self, source_key: str) -> Dict[str, Any]:
        """Runs the standalone metadata analyzer and pins the profile object directly to the Source."""
        from app.metadata_analyzer.analyzer import MetadataAnalyzer
        
        if source_key not in self.source_definitions:
            raise KeyError(f"Source key {source_key} not bound.")
            
        definition = self.source_definitions[source_key]
        patch = self.fetch(source_key=source_key, limit=100)
        
        analyzer = MetadataAnalyzer(source_key=source_key, source_url=definition.source_url)
        profile = analyzer.generate_profile(patch)
        
        # Store metadata natively
        self.metadata[source_key] = profile.model_dump()
        return self.metadata[source_key]

    def run_meta_finder(self, source_key: str) -> Optional[Dict[str, Any]]:
        """Runs the official reconnaissance adapter and pins unified schemas to the Source."""
        from app.metadata_finder.adapter import OfficialMetaAdapter
        from app.metadata_finder.document_registry import DocumentRegistry
        
        if source_key not in self.source_definitions:
            raise KeyError(f"Source key {source_key} not bound.")
            
        registry = DocumentRegistry()
        adapter = OfficialMetaAdapter(registry)
        
        unified_meta = None
        if source_key in registry.registry:
             unified_meta = adapter.extract_unified_meta(source_key)
             
        if unified_meta:
            self.metadata[f"{source_key}_official"] = unified_meta
            
        return unified_meta

def source(key_or_def: str | SourceDefinition) -> Source:
    return Source(key_or_def)

def analysis_tools() -> AnalysisTools:
    return AnalysisTools()

class AnalysisTools:
    pass

class Charts:
    pass

def charts() -> Charts:
    return Charts()

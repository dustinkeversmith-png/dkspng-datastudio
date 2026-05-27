"""Source schema objects used by registry entries and connectors."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceDefinition:
    """Minimal dataset definition needed to fetch and describe a source."""

    source_key: str
    display_name: str
    category: str
    connector_type: str
    source_url: str
    notes: str = ""
    requires_download: bool = False

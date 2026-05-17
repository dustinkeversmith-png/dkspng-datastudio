"""Column object — a lightweight Series wrapper returned from Source.map()."""
from __future__ import annotations
import pandas as pd


class Column:
    """A named series slice produced by applying a registered mapping."""

    def __init__(self, name: str, data: pd.Series, source_key: str, mapping_name: str = ""):
        self.name = name
        self.data = data
        self.source_key = source_key
        self.mapping_name = mapping_name

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return (
            f"Column(name={self.name!r}, source={self.source_key!r}, "
            f"mapping={self.mapping_name!r}, rows={len(self.data)})"
        )

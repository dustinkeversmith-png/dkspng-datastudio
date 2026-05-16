from pydantic import BaseModel
from typing import List, Optional

class ColumnProfile(BaseModel):
    name: str
    inferred_type: str
    inferred_unit_tag: Optional[str] = None
    null_count: int = 0
    unique_values: int = 0
    human_description: Optional[str] = None

class DatasetProfile(BaseModel):
    source_key: str
    source_url: str
    documentation_url: Optional[str] = None
    fetch_timestamp: str
    row_count: int
    columns: List[ColumnProfile]

    def export_to_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

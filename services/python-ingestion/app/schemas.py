from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel


class RegionalObservationCreate(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    dataset_category: str
    observation_type: Optional[str] = None

    observed_at: Optional[datetime] = None
    year: Optional[int] = None

    state: str = "Oregon"
    county: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    unit: Optional[str] = None

    confidence_level: Optional[str] = None
    raw_properties_json: dict[str, Any] = {}


class IngestionResult(BaseModel):
    source_name: str
    inserted_count: int
    skipped_count: int
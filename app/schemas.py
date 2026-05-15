from typing import Any

from pydantic import BaseModel, Field


class SourceDefinition(BaseModel):
    source_key: str
    display_name: str
    category: str
    connector_type: str
    source_url: str
    notes: str | None = None
    latitude_fields: list[str] = Field(default_factory=lambda: ["latitude", "lat", "y"])
    longitude_fields: list[str] = Field(default_factory=lambda: ["longitude", "lon", "lng", "x"])
    year_fields: list[str] = Field(default_factory=lambda: ["year", "fire_year", "incident_year"])
    county_fields: list[str] = Field(default_factory=lambda: ["county", "county_name"])


class IngestionResult(BaseModel):
    source_key: str
    status: str
    rows_read: int
    rows_written: int
    error_message: str | None = None


class AddDatasetRequest(BaseModel):
    dataset_id: str = Field(description="Stable id for this dataset within the visualization session")
    source_key: str = Field(description="Registered source key from /sources")


class PipelineUpdateRequest(BaseModel):
    steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered manipulation steps (exclude_columns, include_columns, rename_columns, join)",
    )


class BufferCommandRequest(BaseModel):
    command: dict[str, Any]


class BufferApplyRequest(BaseModel):
    clear_after_apply: bool = True


class CreateSessionRequest(BaseModel):
    label: str | None = Field(default=None, description="Optional human-readable session label")


class VisualizationSessionSummary(BaseModel):
    session_id: str
    label: str | None = None
    datasets: dict[str, str] = Field(description="dataset_id -> source_key")
    pipeline_step_count: int
    buffer_step_count: int = 0
    chart_count: int = 0
    saved_snapshot_count: int = 0


class SourceRegistryUpsertRequest(BaseModel):
    source_key: str
    display_name: str
    category: str
    connector_type: str
    source_url: str
    notes: str | None = None
    latitude_fields: list[str] = Field(default_factory=lambda: ["latitude", "lat", "y"])
    longitude_fields: list[str] = Field(default_factory=lambda: ["longitude", "lon", "lng", "x"])
    year_fields: list[str] = Field(default_factory=lambda: ["year", "fire_year", "incident_year"])
    county_fields: list[str] = Field(default_factory=lambda: ["county", "county_name"])


class DatasetVerifyResult(BaseModel):
    dataset_id: str
    source_key: str
    row_count: int
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    truncated: bool = False


class ChartUpsertRequest(BaseModel):
    chart: dict[str, Any]


class SnapshotAppendRequest(BaseModel):
    """Payload compatible with ``SaveSnapshotSpec`` (``type``, ``name``, optional flags)."""

    snapshot: dict[str, Any]

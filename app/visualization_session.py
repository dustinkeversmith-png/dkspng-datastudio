"""In-memory VisualizationSession registry and dataset bindings."""

from __future__ import annotations

import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.source_registry import get_source


_DATASET_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")


class SessionDatasetBinding(BaseModel):
    """Maps a user-defined dataset id to a registered source."""

    dataset_id: str
    source_key: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VisualizationSession(BaseModel):
    session_id: str
    label: str | None = None
    datasets: dict[str, SessionDatasetBinding] = Field(default_factory=dict)
    pipeline: list[dict[str, Any]] = Field(default_factory=list)
    command_buffer: list[dict[str, Any]] = Field(default_factory=list)
    chart_definitions: list[dict[str, Any]] = Field(default_factory=list)
    saved_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    #: Defaults merged into every observation query (geo, year span, text search, …).
    query_profile: dict[str, Any] = Field(default_factory=dict)
    #: Per-``source_key`` overrides for multi-source sessions (e.g. one ``near()`` per feed).
    source_query_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)


_store: dict[str, VisualizationSession] = {}
_lock = threading.Lock()


def validate_dataset_id(dataset_id: str) -> None:
    if not _DATASET_ID_RE.match(dataset_id):
        raise ValueError(
            "dataset_id must start with a letter and contain only letters, digits, underscore, hyphen (max 64 chars)."
        )


def create_session(label: str | None = None) -> VisualizationSession:
    session_id = str(uuid.uuid4())
    session = VisualizationSession(session_id=session_id, label=label)
    with _lock:
        _store[session_id] = session
    return session


def get_session(session_id: str) -> VisualizationSession:
    with _lock:
        found = _store.get(session_id)
    if not found:
        raise KeyError(f"Unknown visualization session: {session_id}")
    return found


def delete_session(session_id: str) -> None:
    with _lock:
        _store.pop(session_id, None)


def add_dataset(session_id: str, dataset_id: str, source_key: str) -> VisualizationSession:
    validate_dataset_id(dataset_id)
    get_source(source_key)

    session = get_session(session_id)
    binding = SessionDatasetBinding(dataset_id=dataset_id, source_key=source_key)

    with _lock:
        stored = _store[session_id]
        datasets = dict(stored.datasets)
        datasets[dataset_id] = binding
        updated = stored.model_copy(update={"datasets": datasets})
        _store[session_id] = updated

    return updated


def remove_dataset(session_id: str, dataset_id: str) -> VisualizationSession:
    session = get_session(session_id)
    with _lock:
        stored = _store[session_id]
        datasets = dict(stored.datasets)
        datasets.pop(dataset_id, None)
        updated = stored.model_copy(update={"datasets": datasets})
        _store[session_id] = updated
    return updated


def set_pipeline(session_id: str, steps: list) -> VisualizationSession:
    session = get_session(session_id)
    with _lock:
        stored = _store[session_id]
        updated = stored.model_copy(update={"pipeline": list(steps)})
        _store[session_id] = updated
    return updated


def get_buffer(session_id: str) -> list[dict[str, Any]]:
    session = get_session(session_id)
    return list(session.command_buffer)


def append_buffer_command(session_id: str, command: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        next_buffer = list(stored.command_buffer)
        next_buffer.append(dict(command))
        updated = stored.model_copy(update={"command_buffer": next_buffer})
        _store[session_id] = updated
    return updated


def clear_buffer(session_id: str) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        updated = stored.model_copy(update={"command_buffer": []})
        _store[session_id] = updated
    return updated


def apply_buffer_to_pipeline(session_id: str, clear_after_apply: bool = True) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        merged = list(stored.pipeline) + list(stored.command_buffer)
        updated = stored.model_copy(
            update={
                "pipeline": merged,
                "command_buffer": [] if clear_after_apply else list(stored.command_buffer),
            }
        )
        _store[session_id] = updated
    return updated


def list_sessions() -> list[VisualizationSession]:
    with _lock:
        return list(_store.values())


def append_chart_definition(session_id: str, chart: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        next_charts = list(stored.chart_definitions)
        next_charts.append(dict(chart))
        updated = stored.model_copy(update={"chart_definitions": next_charts})
        _store[session_id] = updated
    return updated


def append_saved_snapshot(session_id: str, snapshot: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        next_snaps = list(stored.saved_snapshots)
        next_snaps.append(dict(snapshot))
        updated = stored.model_copy(update={"saved_snapshots": next_snaps})
        _store[session_id] = updated
    return updated


def clear_charts(session_id: str) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        updated = stored.model_copy(update={"chart_definitions": []})
        _store[session_id] = updated
    return updated


def clear_saved_snapshots(session_id: str) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        updated = stored.model_copy(update={"saved_snapshots": []})
        _store[session_id] = updated
    return updated


def set_query_profile(session_id: str, profile: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        updated = stored.model_copy(update={"query_profile": dict(profile)})
        _store[session_id] = updated
    return updated


def merge_query_profile(session_id: str, patch: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        merged = {**stored.query_profile, **patch}
        updated = stored.model_copy(update={"query_profile": merged})
        _store[session_id] = updated
    return updated


def set_source_query_profile(session_id: str, source_key: str, profile: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        nxt = dict(stored.source_query_profiles)
        nxt[source_key] = dict(profile)
        updated = stored.model_copy(update={"source_query_profiles": nxt})
        _store[session_id] = updated
    return updated


def merge_source_query_profile(session_id: str, source_key: str, patch: dict[str, Any]) -> VisualizationSession:
    get_session(session_id)
    with _lock:
        stored = _store[session_id]
        nxt = dict(stored.source_query_profiles)
        cur = dict(nxt.get(source_key, {}))
        cur.update(patch)
        nxt[source_key] = cur
        updated = stored.model_copy(update={"source_query_profiles": nxt})
        _store[session_id] = updated
    return updated

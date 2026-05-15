# Natural API / Dataset Intake — Visualization Session

This document describes the **VisualizationSession**–based workflow for combining registered sources, validating what you loaded, shaping rows with a **processing pipeline**, and driving charts and exports from **session context** instead of a single `source_key`.

---

## Concepts

| Term | Meaning |
|------|---------|
| **Registered source** | An entry in the source registry (`GET /sources`) with a stable `source_key`. Data still lives in `regional_observations` after ingestion. |
| **Visualization session** | An in-memory bucket on the API server: a UUID `session_id`, a map of **dataset ids** → **source_key**, and an ordered **pipeline** of manipulation steps. |
| **Dataset id** | Your label for one binding inside a session (for example `fires`, `slides`). It appears as `session_dataset_id` on merged rows. |
| **Pipeline** | Steps such as excluding columns, keeping only certain columns, renaming, or joining two dataset streams on shared keys. Applied after rows from each binding are loaded and tagged. |

**Persistence:** Sessions are stored **in process memory**. Restarting the API clears them. Persist `session_id` (and pipeline JSON if you use it) in your client or automation if you need repeatability.

---

## HTTP API

Base URL examples use `http://127.0.0.1:8000`.

### Create a session

```http
POST /session
Content-Type: application/json

{"label": "Optional label"}
```

Response includes `session_id`, `datasets`, and `pipeline_step_count`.

### AddDataset — bind a registry source under your id

```http
POST /session/{session_id}/datasets
Content-Type: application/json

{"dataset_id": "fires_a", "source_key": "odf_fire_occurrence"}
```

`dataset_id` must match `^[a-zA-Z][a-zA-Z0-9_-]{0,63}$`.

### Configure the manipulation pipeline

```http
PUT /session/{session_id}/pipeline
Content-Type: application/json

{
  "steps": [
    {"type": "exclude_columns", "columns": ["raw_properties_json"]},
    {"type": "include_columns", "columns": ["year", "county", "metric_value"], "dataset_id": "fires_a"}
  ]
}
```

Step types:

- **`exclude_columns`** — Drop listed columns (optional `dataset_id` scopes rows).
- **`include_columns`** — Keep only listed columns plus identifiers (`session_dataset_id`, `source_key`, `id`).
- **`rename_columns`** — `mapping` of old → new name (optional `dataset_id`).
- **`join`** — Merge rows from two dataset ids on `on` keys; supports `how`: `inner` \| `left` \| `outer`.

### Verify one binding (columns + sample rows)

Reads directly from the database for that **source_key** (not the merged pipeline):

```http
GET /session/{session_id}/datasets/{dataset_id}/verify
```

### Preview merged session rows (filters + pipeline)

```http
GET /session/{session_id}/preview?limit=50&county=Multnomah
```

### Query & export using session context

Any endpoint that previously accepted `source_key` now accepts **`session_id`** as an alternative. When `session_id` is set, the backend loads rows for **each** binding, tags them with `session_dataset_id`, applies the session pipeline, and applies `limit` to the combined result.

Examples:

```http
GET /observations/query?session_id={uuid}&limit=500
GET /exports/observations.csv?session_id={uuid}
GET /comparison/datasets?session_id={uuid}
GET /analysis/correlation?session_id={uuid}
GET /comparison/sankey?session_id={uuid}
```

Legacy behavior remains: pass `source_key` (and no `session_id`) for a single-source query.

---

## CLI (`python -m app.cli`)

From the `regional-data-studio` directory with `PYTHONPATH` including `app` (or run as documented in your environment):

| Command | Purpose |
|---------|---------|
| `python -m app.cli session create` | Calls **`POST /session`** on `http://127.0.0.1:8000` (requires API running). |
| `python -m app.cli session add-dataset SESSION_UUID --id fires_a --source odf_fire_occurrence` | **`POST /session/{id}/datasets`**. |
| `python -m app.cli session verify SESSION_UUID --id fires_a` | Local DB verification (needs DB env); does not require HTTP. |
| `python -m app.cli session preview SESSION_UUID` | **`GET /session/.../preview`**. |
| `python -m app.cli session create-local` | Creates a session in the **same Python process** only (for tests). |
| `python -m app.cli session add-dataset-local …` | Adds binding in-process (dev only). |
| `python -m app.cli session show SESSION_UUID` | Prints in-process session state (only if store is shared with the server process). |

---

## Web dashboard

1. Click **New session** → stores `session_id` in browser `localStorage`.
2. Select sources with checkboxes → **Register checked sources** → issues AddDataset for each with `dataset_id` derived from `source_key`.
3. Enable **Use visualization session for queries & exports** → filters, CSV export, and comparison calls use `session_id` instead of a single `source_key`.

Ingestion still uses **Ingest Selected Source** with the county/year dropdown `source_key` field when you need to load data into `regional_observations`.

---

## Design notes

- **Multi-source limits:** The session loader splits the observation `limit` across bindings (`limit // n`) before merging, then truncates to `limit` after the pipeline.
- **Comparison API:** `GET /comparison/datasets` accepts either comma-separated `source_keys` **or** `session_id` (at least two datasets required).

For schema details, open the interactive docs at `http://127.0.0.1:8000/docs` after starting the API.

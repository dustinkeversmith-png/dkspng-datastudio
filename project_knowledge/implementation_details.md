# Regional Data Studio: Implementation Details

The Regional Data Studio is a multi-phase project designed to ingest, process, analyze, and visualize regional datasets for Oregon. The system is built with a backend in Python (FastAPI) and a frontend dashboard in React + Vite, enhanced with R and MATLAB analysis integrations.

## Architecture & Phases

The system has been developed across 5 distinct phases, adding architectural layers progressively:

### Phase 1: Ingestion Backend
- **Core Technology:** Python FastAPI, PostgreSQL with PostGIS, Docker Compose.
- **Functionality:** Source registry and generic REST ingestion for CSV, Excel, GeoJSON, and ArcGIS.
- **Data Schema:** Normalized `regional_observations` table for structured storage.
- **Tools:** CLI ingestion runner (`python -m app.cli`) and dataset refresh endpoints.

### Phase 2: Core Dashboard & Filtering
- **Frontend:** React + Vite dashboard (`apps/web-dashboard`).
- **Functionality:** Region-filtered observation API, dataset and county selectors, year range fields.
- **Visualizations:** Scatter plot, county bar chart, and metric trend charts.
- **Exporting:** CSV export endpoints (`/exports/observations.csv`).

### Phase 3: R Analysis Layer
- **Integration:** Python backend calls an external R process (`Rscript`) via temporary CSV exports.
- **Capabilities:** Correlation matrix, simple linear regression, and county comparisons.
- **Files:** Found in `services/r-analysis/` (e.g., `correlation.R`, `regression.R`).
- **Error Handling:** Gracefully handles missing R installations by returning clear errors to the client.

### Phase 4: MATLAB Modeling Layer
- **Integration:** MATLAB Engine API for Python, with a built-in Python fallback.
- **Capabilities:** Risk surface modeling, spatial interpolation, and matrix comparison endpoints (`/modeling/...`).
- **Resilience:** The modeling runner defaults to a safe Python fallback mode if the MATLAB engine is not installed, preventing development blockers.

### Phase 5: Cross-Domain Comparison & Workflows
- **Functionality:** Cross-domain comparison engine and Sankey diagram workflow layer.
- **Capabilities:** Dataset/category/county/metric rollups, comparison presets, and a dashboard Sankey chart visualization.

## Natural API / Dataset Intake

The system employs a **Visualization Session** workflow for combining and shaping rows before charting or exporting.

- **Sessions:** In-memory buckets (`session_id`) on the API server that hold dataset bindings and an ordered manipulation pipeline.
- **Bindings:** Mapping of a custom `dataset_id` (e.g., `fires_a`) to a registered `source_key`.
- **Pipelines:** Configurable steps to shape data, including `exclude_columns`, `include_columns`, `rename_columns`, and `join` operations (inner/left/outer).
- **Execution:** Endpoints querying by `session_id` load rows for all bindings, apply the session pipeline across the streams, and return a combined payload.

## Infrastructure Dependencies

- **Database:** PostgreSQL + PostGIS (via Docker Compose).
- **Python:** Python 3.x with dependencies defined in `requirements.txt`.
- **Node.js:** NPM for the `apps/web-dashboard`.
- **Optional Tools:** R environment for Phase 3 analysis, MATLAB Engine for Phase 4 modeling.

# Regional Data Studio: Usage Documentation

This guide provides instructions on how to set up, run, and interact with the Regional Data Studio application.

## Prerequisites
- Docker (for running PostgreSQL and PostGIS)
- Python 3.x
- Node.js and npm
- (Optional) R environment and RStudio
- (Optional) MATLAB Engine API for Python

## 1. Starting the Database

The application uses Docker Compose to run a PostgreSQL database with PostGIS extensions.

```bash
docker compose up -d
```

## 2. Backend Setup & Ingestion

Set up a Python virtual environment, install dependencies, and start the FastAPI server.

```bash
# Set up environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

# Ingest sample data
python -m app.cli sources
python -m app.cli ingest generic_csv_sample

# Start the API server
uvicorn app.main:app --reload
```

You can view the interactive API documentation at: `http://127.0.0.1:8000/docs`

## 3. Web Dashboard Setup

The React frontend requires Node.js.

```bash
cd apps/web-dashboard
npm install
npm run dev
```

Open the Vite URL in your browser: `http://127.0.0.1:5173`

## 4. Querying the API

You can query the backend API using basic HTTP GET requests.

**Query by County:**
```bash
curl "http://127.0.0.1:8000/observations/query?county=Multnomah"
```

**Query by Dataset and Year:**
```bash
curl "http://127.0.0.1:8000/observations/query?source_key=generic_csv_sample&year_min=2021&year_max=2023"
```

**Export as CSV:**
```bash
curl -L "http://127.0.0.1:8000/exports/observations.csv?county=Multnomah" -o multnomah.csv
```

## 5. Working with Visualization Sessions (Natural API)

The API supports "sessions" to create complex queries, merges, and transformations across multiple datasets.

**Create a Session:**
```bash
python -m app.cli session create
```

**Bind a Dataset to the Session:**
```bash
python -m app.cli session add-dataset <SESSION_UUID> --id fires_a --source generic_csv_sample
```

**Preview Merged Session Rows:**
```bash
python -m app.cli session preview <SESSION_UUID>
```

When using the API, pass `session_id={uuid}` instead of `source_key` to utilize the session context for queries, exports, and analysis endpoints.

## 6. Advanced Analysis Endpoints

The backend exposes endpoints that run R and MATLAB algorithms on the ingested data.

**R-Backed Analysis (Phase 3):**
*Requires installing R packages: `jsonlite`, `dplyr`, `tidyr`, `readr`, `ggplot2`, `broom`, `rmarkdown`*
```bash
# Correlation
curl "http://127.0.0.1:8000/analysis/correlation?source_key=generic_csv_sample"

# Regression
curl "http://127.0.0.1:8000/analysis/regression?source_key=generic_csv_sample&x=year&y=metric_value"
```

**MATLAB-Backed Modeling (Phase 4):**
*Defaults to a Python fallback if MATLAB Engine is not installed.*
```bash
# Risk Surface
curl "http://127.0.0.1:8000/modeling/risk-surface?source_key=generic_csv_sample"

# Spatial Interpolation
curl "http://127.0.0.1:8000/modeling/spatial-interpolation?source_key=generic_csv_sample"
```

**Cross-Domain Compare & Sankey Flow (Phase 5):**
```bash
# Cross-Domain
curl "http://127.0.0.1:8000/comparison/cross-domain?source_key=generic_csv_sample"

# Sankey
curl "http://127.0.0.1:8000/comparison/sankey?source_key=generic_csv_sample"
```

## Using the Web Dashboard

1. Navigate to `http://127.0.0.1:5173`.
2. Select **Datasets**, **Counties**, and **Year Range**.
3. Click **Apply Filter** to populate the Scatter Plot, County Chart, and Metric Trend panels.
4. Click analysis action buttons (e.g., `Run Correlation`, `Run Interpolation`, `Build Sankey`) to fetch advanced modeling results from the backend.
5. Click **New Session** to bundle registered sources into a visualization session and apply pipeline transformations directly from the UI.

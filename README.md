# Regional Data Studio — Phase 1 Backend

Phase 1 creates the ingestion backend for Oregon regional datasets.

## Includes

- Python FastAPI backend
- Source registry
- Generic CSV/Excel/GeoJSON/ArcGIS REST ingestion
- PostGIS schema
- Normalized `regional_observations` table
- Dataset refresh endpoints
- CLI ingestion runner
- Docker Compose for PostgreSQL + PostGIS

## Quick start

```bash
cd regional-data-studio-phase1

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

docker compose up -d

copy .env.example .env

python -m app.cli sources
python -m app.cli ingest generic_csv_sample

uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

The ODF and SLIDO entries are intentionally configured with placeholder URLs until you paste in the exact ArcGIS REST query endpoint.

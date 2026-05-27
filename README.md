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

# Phase 1 usage snippet

## 2. Install and run the backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python -m app.cli sources
python -m app.cli ingest generic_csv_sample

uvicorn app.main:app --reload
```

## 5. Open the dashboard

```bash
cd apps/web-dashboard
npm install
npm run dev
```


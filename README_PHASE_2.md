# Regional Data Studio — Phase 2 Patch

Phase 2 adds:

- Region-filtered observation API
- CSV export endpoint
- React + Vite dashboard
- Dataset selector
- County selector
- Year range fields
- Scatter plot
- County bar chart
- Metric trend chart
- Placeholders for heat map, correlation matrix, and Sankey diagram

## Apply patch

Copy this patch folder into the Phase 1 project root:

```bash
xcopy /E /I /Y regional-data-studio-phase2-patch\* regional-data-studio-phase1\
```

## Backend

```bash
docker compose up -d
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli ingest generic_csv_sample
uvicorn app.main:app --reload
```

## Frontend

```bash
cd apps/web-dashboard
npm install
npm run dev
```

## Test URLs

```text
http://127.0.0.1:8000/sources
http://127.0.0.1:8000/regions
http://127.0.0.1:8000/observations/query?county=Multnomah
http://127.0.0.1:8000/exports/observations.csv?county=Multnomah
```

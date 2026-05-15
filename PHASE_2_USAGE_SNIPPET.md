# Phase 2 usage snippet

Phase 2 adds the dashboard and region-filtered API routes.

## 1. Apply Phase 2 patch

From the folder containing both projects:

```bash
xcopy /E /I /Y regional-data-studio-phase2-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## 2. Start the backend

```bash
docker compose up -d

.venv\Scripts\activate
pip install -r requirements.txt

python -m app.cli ingest generic_csv_sample
uvicorn app.main:app --reload
```

## 3. Verify the backend

Open these URLs:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/sources
http://127.0.0.1:8000/regions
http://127.0.0.1:8000/observations/query
```

Query one county:

```bash
curl "http://127.0.0.1:8000/observations/query?county=Multnomah"
```

Query by year:

```bash
curl "http://127.0.0.1:8000/observations/query?year_min=2021&year_max=2023"
```

Query by dataset and county:

```bash
curl "http://127.0.0.1:8000/observations/query?source_key=generic_csv_sample&county=Lane"
```

Export CSV:

```bash
curl -L "http://127.0.0.1:8000/exports/observations.csv?county=Multnomah" -o multnomah.csv
```

## 4. Start the dashboard

```bash
cd apps\web-dashboard
npm install
npm run dev
```

Open the Vite URL:

```text
http://127.0.0.1:5173
```

## 5. Use the dashboard

1. Select a dataset.
2. Select a county.
3. Optionally enter a year range.
4. Click `Apply Filter`.
5. Review:
   - Scatter Plot
   - County Chart
   - Metric Trend
6. Click `Export CSV` to download the filtered records.

## 6. Current Phase 2 limitations

The heat map, correlation matrix, and Sankey panels are scaffold placeholders.

Phase 3 fills in the analysis side by adding:

```text
- R-backed correlation endpoint
- R-backed regression endpoint
- county comparison endpoint
- report generation hooks
```

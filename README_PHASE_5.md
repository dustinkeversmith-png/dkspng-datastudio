# Regional Data Studio — Phase 5 Patch

Phase 5 adds the cross-domain comparison engine and Sankey workflow layer.

## Adds

```text
app/comparison.py
app/main.py
apps/web-dashboard/src/App.tsx
apps/web-dashboard/src/styles.css
tests/test_comparison.py
```

## Capabilities

- Sankey flow endpoint
- Cross-domain comparison endpoint
- Dataset/category/county/metric rollups
- Comparison presets endpoint
- Dashboard Sankey chart
- Dashboard comparison JSON panel

## Apply patch

```bash
xcopy /E /I /Y regional-data-studio-phase5-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## Backend

```bash
docker compose up -d
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli ingest generic_csv_sample
uvicorn app.main:app --reload
```

## Test endpoints

```text
http://127.0.0.1:8000/comparison/presets
http://127.0.0.1:8000/comparison/sankey?source_key=generic_csv_sample
http://127.0.0.1:8000/comparison/cross-domain?source_key=generic_csv_sample
```

## Dashboard

```bash
cd apps\web-dashboard
npm install
npm run dev
```

Then click:

```text
Build Sankey
Run Cross-Domain Compare
```

## Design note

Phase 5 does not require multiple real datasets to function. It works with the sample dataset and scales up when ODF, SLIDO, traffic, and workforce datasets are added.

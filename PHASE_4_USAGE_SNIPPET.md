# Phase 4 usage snippet

Phase 4 adds MATLAB-style modeling endpoints with a Python fallback.

## 1. Apply Phase 4 patch

```bash
xcopy /E /I /Y regional-data-studio-phase4-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## 2. Optional MATLAB setup

Phase 4 runs without MATLAB because the modeling runner has a Python fallback.

If you want real MATLAB Engine support:

```bash
cd "C:\Program Files\MATLAB\R2024b\extern\engines\python"
python -m pip install .
```

Verify:

```bash
python -c "import matlab.engine; print('MATLAB Engine OK')"
```

## 3. Start backend

```bash
docker compose up -d

.venv\Scripts\activate
pip install -r requirements.txt

python -m app.cli ingest generic_csv_sample
uvicorn app.main:app --reload
```

## 4. Test modeling endpoints

Risk surface:

```bash
curl "http://127.0.0.1:8000/modeling/risk-surface?source_key=generic_csv_sample"
```

Spatial interpolation:

```bash
curl "http://127.0.0.1:8000/modeling/spatial-interpolation?source_key=generic_csv_sample"
```

Matrix comparison:

```bash
curl "http://127.0.0.1:8000/modeling/matrix-compare?source_key=generic_csv_sample"
```

## 5. Start dashboard

```bash
cd apps\web-dashboard
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 6. Use Phase 4 dashboard

1. Select a dataset.
2. Select county/year filters.
3. Click `Apply Filter`.
4. Click:
   - `Run Risk Surface`
   - `Run Interpolation`
   - `Run Matrix Compare`
5. Review the heat map and JSON model result.

## 7. Phase 5 goal

Phase 5 adds:

```text
- Sankey diagram builder
- cross-domain comparison workflow
- source → category → county → metric flow
- comparison presets
- dashboard Sankey visualization
```

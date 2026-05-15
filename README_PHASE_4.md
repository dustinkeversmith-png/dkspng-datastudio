# Regional Data Studio — Phase 4 Patch

Phase 4 adds the MATLAB modeling layer.

## Adds

```text
services/matlab-modeling/
  matlab_model_runner.py
  matlab_scripts/
    risk_surface.m
    spatial_interpolation.m
    matrix_compare.m

app/matlab_modeling.py
app/main.py
apps/web-dashboard/src/App.tsx
```

## Capabilities

- Risk surface model endpoint
- Spatial interpolation endpoint
- Matrix comparison endpoint
- MATLAB Engine support when available
- Python fallback implementation when MATLAB is not installed
- Dashboard buttons for modeling calls

## Apply patch

```bash
xcopy /E /I /Y regional-data-studio-phase4-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## Optional MATLAB setup

Phase 4 works without MATLAB using the Python fallback.

For real MATLAB execution, install MATLAB and the MATLAB Engine API for Python.

Inside the MATLAB engine folder, this usually looks like:

```bash
cd "C:\Program Files\MATLAB\R2024b\extern\engines\python"
python -m pip install .
```

Then verify:

```bash
python -c "import matlab.engine; print('MATLAB Engine OK')"
```

## Backend test

```bash
uvicorn app.main:app --reload
```

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

## Dashboard

```bash
cd apps\web-dashboard
npm install
npm run dev
```

Then use:

```text
Run Risk Surface
Run Interpolation
Run Matrix Compare
```

## Design note

The Python backend exports filtered observations to temporary CSV, calls a modeling runner, and returns JSON.

The modeling runner tries MATLAB first when requested, but defaults to safe Python fallback mode so development does not block if MATLAB is unavailable.

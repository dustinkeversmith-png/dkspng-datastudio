# Phase 3 usage snippet

Phase 3 adds the R analysis service.

## 1. Apply Phase 3 patch

```bash
xcopy /E /I /Y regional-data-studio-phase3-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## 2. Install R packages

Open R or RStudio:

```r
install.packages(c(
  "jsonlite",
  "dplyr",
  "tidyr",
  "readr",
  "ggplot2",
  "broom",
  "rmarkdown"
))
```

Make sure `Rscript` works from your terminal:

```bash
Rscript --version
```

## 3. Start backend

```bash
docker compose up -d

.venv\Scripts\activate
pip install -r requirements.txt

python -m app.cli ingest generic_csv_sample
uvicorn app.main:app --reload
```

## 4. Test R-backed analysis endpoints

Correlation:

```bash
curl "http://127.0.0.1:8000/analysis/correlation?source_key=generic_csv_sample"
```

Regression:

```bash
curl "http://127.0.0.1:8000/analysis/regression?source_key=generic_csv_sample&x=year&y=metric_value"
```

County comparison:

```bash
curl "http://127.0.0.1:8000/analysis/county-compare?source_key=generic_csv_sample"
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

## 6. Use Phase 3 dashboard

1. Select `Generic Regional CSV`.
2. Select a county or leave county empty.
3. Click `Apply Filter`.
4. Click:
   - `Run Correlation`
   - `Run Regression`
   - `Compare Counties`
5. Review the JSON result panel.

## 7. Current Phase 3 limitation

The R result is returned as JSON and displayed raw.

Phase 4 adds MATLAB-backed modeling endpoints for:

```text
- spatial interpolation
- risk surface generation
- matrix comparison
- numerical simulation hooks
```

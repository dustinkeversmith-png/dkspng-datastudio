# Regional Data Studio — Phase 3 Patch

Phase 3 adds the R analysis layer.

## Adds

```text
services/r-analysis/
  analysis_runner.R
  correlation.R
  regression.R
  county_compare.R
  report_template.Rmd

app/analysis.py
app/main.py
apps/web-dashboard/src/App.tsx
```

## Capabilities

- Correlation matrix endpoint
- Simple linear regression endpoint
- County comparison endpoint
- RMarkdown report script scaffold
- Dashboard buttons for analysis calls

## Apply patch

```bash
xcopy /E /I /Y regional-data-studio-phase3-patch\* regional-data-studio-phase1\
cd regional-data-studio-phase1
```

## Python requirements

Phase 3 uses the existing Python backend. No new Python package is required.

## R requirements

Install R, then install these R packages:

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

## Test backend

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/analysis/correlation?source_key=generic_csv_sample
http://127.0.0.1:8000/analysis/regression?source_key=generic_csv_sample&x=year&y=metric_value
http://127.0.0.1:8000/analysis/county-compare?source_key=generic_csv_sample
```

## Notes

The Python backend exports filtered observations to a temporary CSV, calls Rscript, and returns JSON.

If R is not installed or `Rscript` is not on PATH, the analysis endpoints return a clear error.

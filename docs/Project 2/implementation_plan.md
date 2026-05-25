# Project 2 — Phase 2 Implementation Plan
## Sampling · Cross-Source Spatial Analysis · Predictive Modeling · Advanced Plots

### Background

The existing `project_2.py` fetches sources, applies a 50-mile Grants Pass distance filter, and collects metadata. The live `project2_metadata.json` confirms four rich sources succeeded:

| Source | Rows | Lat/Lon | Key Fields |
|---|---|---|---|
| `nifc_wildfire_incidents` | 2000 (17 local) | `latitude`, `longitude` | `IncidentSize`, `FireCause`, `FireDiscoveryDateTime` |
| `noaa_gsod` | 365 | `LATITUDE`, `LONGITUDE` | `TEMP`, `GUST`, `PRCP`, `VISIB`, `DATE` |
| `epa_air_quality` | ~365k | `county Name`, `State Name` | `AQI`, `Category`, `Date` |
| `portal_odf_firestats` | ~50k | `lat_dd`, `long_dd` | `specificcause`, `esttotalacres`, `fireyear` |
| `portal_dogami_slido` | varies | `latitude`, `longitude` | `CONTR_FACT`, `AREA_ft2`, `VOLUME_ft3`, `DEEP_SHAL` |

---

## User Review Required

> [!IMPORTANT]
> **sklearn dependency** — models (`LinearRegression`, `KMeans`, `SVM`, `NaiveBayes`, `DecisionTree`, `PCA`) and Fourier analysis all require `scikit-learn` and `scipy`. These are likely already in requirements.txt (the existing `log_regression`/`knn` in source_binding.py already try-imports sklearn). The implementation will use graceful fallbacks for any missing library.

> [!IMPORTANT]
> **statsmodels for ARIMA** — The ARIMA model requires `statsmodels`. Will be gracefully skipped if not installed.

> [!NOTE]
> **Plot output directory** — All charts will be written to `data/plots/project2/`. Plots are generated using `matplotlib` (already in use in `chart.py`).

> [!NOTE]
> **Neural visual operator / neural data-descriptor model** — The guide mentions "neural" generators. These will be implemented as template-based descriptor generators (rule-based heuristics that emit `VisualDescriptor` JSON), not actual neural networks, since there's no training data or GPU pipeline in scope. The architecture will be forward-compatible.

---

## Proposed Changes

### 1. Sampling Engine — `app/sampling/`

#### [NEW] `app/sampling/__init__.py`
#### [NEW] `app/sampling/sampling_engine.py`
Core `SamplingEngine` class — attached to a DataFrame. Provides:
- `uncertainty_if(target, sample_size, confidence, method)` → `SamplingResult`
- `bias_if(condition, compare_to)` → `SamplingResult`
- `confidence_interval(target, confidence, method)` → `SamplingResult`
- Internal bootstrap, t-interval, and z-interval implementations

#### [NEW] `app/sampling/results.py`
`SamplingResult` dataclass per spec.

---

### 2. Spatial-Temporal Key — `app/neighbors/`

#### [NEW] `app/neighbors/__init__.py`
#### [NEW] `app/neighbors/spatial_temporal_distance.py`
`SpatialTemporalKey` dataclass + distance functions that combine haversine + normalised time distance.

#### [NEW] `app/neighbors/neighbor_engine.py`
`NeighborEngine` wrapping sklearn KNN with spatial-temporal distance. Returns `NeighborResult`.

#### [NEW] `app/neighbors/results.py`
`NeighborResult` dataclass.

---

### 3. Clustering — `app/clustering/`

#### [NEW] `app/clustering/__init__.py`
#### [NEW] `app/clustering/cluster_engine.py`
`ClusterEngine` wrapping sklearn KMeans. Returns `ClusterResult`.

#### [NEW] `app/clustering/results.py`
`ClusterResult` dataclass.

---

### 4. Model System — `app/models/`

#### [NEW] `app/models/__init__.py`
#### [NEW] `app/models/base_model.py`
`BaseModel` ABC with `fit`, `predict`, `evaluate` abstract methods.

#### [NEW] `app/models/model_result.py`
`ModelResult`, `PredictionResult`, `ModelEvaluation` dataclasses.

#### [NEW] `app/models/model_engine.py`
`ModelEngine` — takes a DataFrame + model spec, runs fit/evaluate, logs metrics and produces chart paths.

#### [NEW] `app/models/regression/linear_regression_model.py`
#### [NEW] `app/models/regression/logistic_regression_model.py`
#### [NEW] `app/models/classification/svm_model.py`
#### [NEW] `app/models/classification/naive_bayes_model.py`
#### [NEW] `app/models/classification/decision_tree_model.py`
#### [NEW] `app/models/decomposition/pca_model.py`
#### [NEW] `app/models/time_series/arima_model.py`
#### [NEW] `app/models/signal/fourier_model.py`

Each follows `BaseModel`. All have graceful ImportError fallbacks.

---

### 5. Cross-Source Analysis — `app/cross_analysis/`

#### [NEW] `app/cross_analysis/__init__.py`
#### [NEW] `app/cross_analysis/cross_analysis_spec.py`
`CrossAnalysisSpec` — describes grouping, variable groups, and models to run.

#### [NEW] `app/cross_analysis/cross_analysis_engine.py`
`CrossAnalysisEngine` — merges DataFrames on spatial-temporal keys, generates all pair/group combinations, runs `ModelEngine` on each, collects `CrossAnalysisResult`.

#### [NEW] `app/cross_analysis/cross_analysis_result.py`
`CrossAnalysisResult` — list of `ModelResult`, summary metrics, lineage.

---

### 6. Advanced Plots — `app/advanced_plots/`

#### [NEW] `app/advanced_plots/__init__.py`
#### [NEW] `app/advanced_plots/plot_engine.py`
`PlotEngine` — dispatches to specific plot families, writes PNG to `data/plots/`, returns `VisualObject`.

#### [NEW] `app/advanced_plots/distribution_plots.py`
Implements: `boxplot`, `histplot`, `violinplot`, `rangeplot`, `iqrplot`, `vaseplot`, `skewplot`, `summaryplot`, `box_percentile_plot`.

#### [NEW] `app/advanced_plots/bivariate_plots.py`
Implements: `bagplot`, `rangefinder_boxplot`, `twod_boxplot`, `relplot`.

#### [NEW] `app/advanced_plots/model_plots.py`
Implements: `regression_fit_plot`, `residual_plot`, `prediction_interval_plot`, `confusion_matrix_plot`, `pca_component_plot`, `pca_biplot`, `cluster_map`, `knn_neighborhood_map`, `arima_forecast_plot`, `fourier_spectrum_plot`.

#### [NEW] `app/advanced_plots/uncertainty_plots.py`
Implements: `confidence_interval_plot`, `bootstrap_distribution_plot`, `sampling_bias_plot`, `prediction_uncertainty_plot`.

---

### 7. Visual Operator Backend — `app/visual_ops/`

#### [NEW] `app/visual_ops/__init__.py`
#### [NEW] `app/visual_ops/descriptor_json.py`
`VisualDescriptor` dataclass + `to_json()` method matching the spec format.

#### [NEW] `app/visual_ops/visual_operator_engine.py`
`VisualOperatorEngine` — accepts data + operator list + visual context, applies each operator, emits `VisualDescriptor`.

#### [NEW] `app/visual_ops/operators.py`
All operator classes: `AxisOperator`, `ColorOperator`, `SizeOperator`, `LayerOperator`, `LegendOperator`, `UncertaintyBandOperator`, `ClusterOverlayOperator`, `ModelFitLineOperator`.

#### [NEW] `app/visual_ops/neural_descriptor_generator.py`
`NeuralDescriptorGenerator` — rule-based (heuristic) generator that inspects a `ModelResult` or `ClusterResult` and auto-generates an appropriate `VisualDescriptor` JSON. Forward-compatible with a real neural model.

---

### 8. Complete `project_2.py`

#### [MODIFY] `project_2.py`
Replace the stub comment block in `project2()` with full orchestration:

```python
# Phase 1 — already implemented
register_datasources()
results = test_all_sources()

# Phase 2 — new
sampling_results  = run_sampling_analysis(source_dataframes)
combined_df       = fuse_sources(source_dataframes)
neighbor_result   = run_knn(combined_df)
cluster_result    = run_kmeans(combined_df)
cross_results     = run_cross_analysis(source_dataframes, cluster_result)
whole_group       = run_whole_group_analysis(combined_df)
plots             = generate_all_plots(...)
descriptors       = generate_visual_descriptors(...)
dump_report(...)
```

---

## Verification Plan

### Automated
```powershell
cd "C:\Users\Cutie Magic 500\datastudio"
python project_2.py
```
Success criteria:
- No unhandled exceptions
- `data/plots/project2/` directory populated with PNG files
- `data/project2_report.json` written with all model results and sampling diagnostics
- All sources that returned rows produce at least one sampling result

### Observation
- Confirm KMeans cluster map PNG saved
- Confirm at least one cross-analysis chart saved
- Confirm ARIMA/Fourier graceful fallback if `statsmodels` not installed

---

## Open Questions

> [!NOTE]
> **EPA AQI spatial join** — EPA data has `county Name` + `State Name` but no lat/lon. The cross-analysis engine will join on county name to NIFC/ODF records where possible, and fall back to statewide aggregation. Is that acceptable, or should we add a county-centroid lookup table?

> [!NOTE]
> **NOAA GSOD** — Only one station (Medford, OR). Cross-correlations will treat it as a region-wide weather signal rather than per-point. This is a reasonable approximation for the 50-mile radius. Acceptable?

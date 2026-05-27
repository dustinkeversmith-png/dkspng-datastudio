# Backend Modules

This document enumerates the active `backend.modules` layout and records the main refactors from the older flat `backend.*` package structure.

## Renames and Refactors

- `backend.models.*` moved to `backend.modules.analysis.models.*`.
- `backend.clustering.*` moved into `backend.modules.analysis.models.clustering.clustering_model`.
- `backend.neighbors.*` and `spatial_temporal_distance.py` moved into `backend.modules.analysis.models.clustering.spatial_temporal_model`.
- `backend.sampling.*` moved into `backend.modules.analysis.models.sampling.sampling_model`.
- `backend.analysis.results` was removed. `RegressionResult` now lives beside `LinearRegressionModel`, and `KNNResult` lives beside the spatial-temporal neighbor model.
- `backend.indexing.*` moved into `backend.modules.data.indexing`.
- `backend.mappings.column` moved into `backend.modules.data.mappings.column`.
- Analysis models no longer create plots or chart files. Visualization belongs under `Modules/Visualization`.

## Modules/Sources

### What it does

`Sources` owns dataset definitions and the stateful `Source` container. It loads sources, stores dataframes, generates metadata, supports expression/index access, and exposes convenience operations for adding columns, simple analysis, and chart construction.

### Basic Usage and Whats Included

```python
from backend.modules.sources import SourceDefinition, source

src = source(SourceDefinition(
    source_key="local_demo",
    display_name="Local Demo",
    category="debug",
    connector_type="csv",
    source_url="data/demo.csv",
))
```

Included:

- `schemas.py`: `SourceDefinition`.
- `source_registry.py`: built-in and mutable source registry.
- `source_binding.py`: `Source`, `source()`, dataframe storage, metadata, indexing, expression access, and source-level helpers.
- `column_info/analyzer`: column and dataset profile generation.
- `column_info/finder`: metadata URL discovery, fetching, parsers, and document registry.

## Modules/Data

### What it does

`Data` contains the lower-level data access pieces used by `Sources`: connectors, download/extraction helpers, expression parsing, and simple export helpers.

### Basic Usage and Whats Included

```python
from backend.modules.data.connectors import create_connector
from backend.modules.sources import get_source

df = create_connector(get_source("generic_csv_sample")).fetch()
```

Included:

- `connectors`: connector base class, tabular adapters, ArcGIS REST adapter, ZIP extraction, and connector factory.
- `expressions`: `AxisExpr`, `SourceProxy`, and expression evaluation for computed source columns.
- `indexing`: row and column index parsers used by `Source.index()`.
- `mappings`: the lightweight `Column` container used by `Source.map()` and `Source.append()`.
- `workflow`: `DataExporter` for CSV/JSON output.
- `exports.py`: CSV `StreamingResponse` helper.

## Modules/Analysis

### What it does

`Analysis` contains data and analysis models only. Models fit data, compute metrics, predictions, uncertainty, and lineage, but do not produce plots.

### Basic Usage and Whats Included

```python
from backend.modules.analysis.models import get_model

Model = get_model("sampling_diagnostics")
result = Model().fit(df, None, {"source_key": "demo", "target": "value"})
print(result.metrics)
```

Included:

- `models/base_model.py`: `BaseModel`, `register_model`, `get_model`, and `list_models`.
- `models/model_result.py`: shared `ModelResult`, `PredictionResult`, and `ModelEvaluation`.
- `models/regression`: linear and logistic regression models; `RegressionResult` is colocated with `LinearRegressionModel`.
- `models/classification`: SVM, naive Bayes, and decision tree models.
- `models/decomposition`: PCA model.
- `models/signal`: Fourier model.
- `models/time_series`: ARIMA model.
- `models/clustering`: KMeans clustering, spatial-temporal neighbor model, `ClusterResult`, `NeighborResult`, `KNNResult`, `SpatialTemporalKey`, and distance helpers.
- `models/sampling`: sampling diagnostics and `SamplingResult`.

## Modules/Visualization

### What it does

`Visualization` owns chart construction and rendered plot output. This module is intentionally separate from analysis models so models remain focused on metrics and data results.

### Basic Usage and Whats Included

```python
chart = src.scatter(src["local_demo"]["longitude"], src["local_demo"]["latitude"])
visual = chart.save("artifacts/local_demo_scatter.png")
```

Included:

- `charts/chart.py`: `Chart`, `VisualObject`, and `LegendObject`.
- `charts/bar_chart.py`: bar-chart spec helper.
- `advanced_plots/plot_engine.py`: matplotlib-based analytical plot suite.

# Backend Modules

## Modules/Sources

### What it does

`Sources` owns dataset definitions and the stateful `Source` object. It loads registered sources, stores fetched dataframes, supports subsetting and indexing, attaches metadata, and provides convenience methods for simple analysis and chart construction.

### Basic Usage and Whats Included

```python
from backend.modules.sources import Source, source

fire = source("odf_fire_occurrence")
subset = fire.subset({"odf_fire_occurrence": ["latitude", "longitude"]})
```

Included:

- `schemas.py`: `SourceDefinition`, the dataset definition shared by the registry and connectors.
- `source_registry.py`: Built-in source catalog and helpers for adding, listing, and deleting source definitions.
- `source_binding.py`: `Source`, `source()`, dataframe storage, indexing, metadata generation, analysis helpers, and chart helpers.
- `column_info/analyzer`: Dataset and column profile generation.
- `column_info/finder`: Metadata discovery, fetching, document registry, and source-specific parsers.

## Modules/Data

### What it does

`Data` handles source ingestion, local downloads, ZIP extraction, expression parsing, and export helpers. It is the lower-level layer that `Sources` uses to fetch tabular data and evaluate column expressions.

### Basic Usage and Whats Included

```python
from backend.modules.data.connectors import create_connector
from backend.modules.sources import get_source

connector = create_connector(get_source("odf_fire_occurrence"))
df = connector.fetch()
```

Included:

- `connectors`: Connector base class, CSV/Excel/GeoJSON/SQLite/web API adapters, ArcGIS REST support, ZIP extraction, and connector factory.
- `expressions`: `AxisExpr`, `SourceProxy`, and string expression evaluation for computed columns.
- `workflow`: `DataExporter` helpers for CSV and JSON export.
- `exports.py`: FastAPI CSV response helper for row dictionaries.

## Modules/Analysis

### What it does

`Analysis` provides registered model classes, shared model result types, simple source-level result dataclasses, and model families for regression, classification, decomposition, signal analysis, time series, clustering, sampling, and spatial-temporal neighbors.

### Basic Usage and Whats Included

```python
from backend.modules.analysis.models import get_model

Model = get_model("cluster_kmeans")
result = Model().fit(df, None, {"source_key": "fire", "k": 6})
```

Included:

- `models/base_model.py`: `BaseModel`, `register_model`, `get_model`, and `list_models`.
- `models/model_result.py`: Shared `ModelResult`, `PredictionResult`, and `ModelEvaluation`.
- `models/clustering_model.py`: `ClusterModel` and `ClusterResult` for KMeans clustering.
- `models/spatial_temporal_model.py`: `NeighborModel`, `NeighborResult`, `SpatialTemporalKey`, distance helpers, and key inference.
- `models/sampling_model.py`: `SamplingModel` and `SamplingResult` for uncertainty, bias, and confidence interval diagnostics.
- `models/regression`: Linear and logistic regression models.
- `models/classification`: SVM, naive Bayes, and decision tree models.
- `models/decomposition`: PCA model.
- `models/signal`: Fourier model.
- `models/time_series`: ARIMA model.
- `results.py`: Legacy simple result dataclasses used by `Source.log_regression()` and `Source.knn()`.

## Modules/Visualization

### What it does

`Visualization` contains chart objects and advanced plotting utilities. It turns source expressions and analysis outputs into composable chart specifications or saved matplotlib figures.

### Basic Usage and Whats Included

```python
from backend.modules.visualization import Chart

chart = Chart("scatter", x_expr, y_expr)
visual = chart.save("artifacts/scatter.png")
```

Included:

- `charts/chart.py`: `Chart`, `VisualObject`, and `LegendObject` for composable visual outputs.
- `charts/bar_chart.py`: A lightweight bar-chart specification helper.
- `advanced_plots/plot_engine.py`: Matplotlib Agg plot suite for summaries, correlations, cross-source plots, maps, and other analytical figures.

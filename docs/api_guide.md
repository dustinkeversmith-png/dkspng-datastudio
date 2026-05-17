# Regional Data Studio: API Guide

Welcome to the Regional Data Studio programmatic API! The studio has been entirely decoupled from legacy FastAPI/Database implementations and is now a lightweight, script-driven analytical toolkit.

This guide details the core primitives available for onboarding, extracting, exploring, and documenting regional datasets.

## 1. Core Abstraction: `Source`
The `Source` object is the foundational data node. It manages endpoint definitions, handles dataset grouping, executes connector routines, and holds attached metadata locally in memory.

### Initialization
```python
from app.workflow import source
from app.schemas import SourceDefinition

# 1. Initialize via an existing Registry Key
my_source = source("portal_odf_firestats")

# 2. Initialize directly via a standalone SourceDefinition
custom_def = SourceDefinition(
    source_key="local_csv",
    display_name="Local Output",
    category="test",
    connector_type="csv",
    source_url="./data/output.csv"
)
custom_source = source(custom_def)
```

### Grouping Multiple Definitions
You can merge multiple API definitions into a single `Source` object. When calling actions, the `Source` will execute across all of its bound definitions.
```python
my_source = source("portal_odf_firestats")
my_source.add_source("portal_dogami_slido")

# my_source now tracks two unique REST endpoints.
```

### Fetching Data (`fetch()`)
Bypass the database entirely to retrieve dataframes directly from connectors (ArcGIS MapServers, Socrata Endpoints, remote CSVs).
```python
# Fetches data across all bound sources (max 1000 rows each)
rows = my_source.fetch(limit=100) 

# Fetch from a specific definition bound within the object
odf_rows = my_source.fetch(source_key="portal_odf_firestats", limit=50)
```

*(Note: Legacy filtering properties like `.near()`, `.where()`, and `.between()` exist as functional chainable stubs for backwards compatibility in existing scripts, but fetching now resolves fully over standard Pandas parsing natively).*

---

## 2. Metadata Generation & Profiling
The `Source` object exposes two built-in methods to interrogate and document unknown datasets using the decoupled `metadata_analyzer` and `metadata_finder` subsystems.

### Generating Structural Profiles (`run_meta_analysis`)
Runs a localized patch-fetch to infer column logic (Dates, Coordinates, Financials, Categoricals) structurally.

```python
profile_dict = my_source.run_meta_analysis("portal_odf_firestats")

# The profile is now pinned to the Source.
print(my_source.metadata["portal_odf_firestats"]) 
# -> { "columns": [ { "name": "latitude", "inferred_type": "float", "inferred_unit_tag": "decimal_degrees", ... } ] }
```

### Scraping Official Meta Docs (`run_meta_finder`)
Attempts to match the source URL to a known external Data Dictionary standard (e.g. ArcGIS `pjson` definitions or Socrata view schemas) and unifies it.
```python
# Searches the internet for official schema mappings
official_meta = my_source.run_meta_finder("portal_dogami_slido")

# The unified dictionary is pinned if found.
print(my_source.metadata["portal_dogami_slido_official"])
```

---

## 3. Data Exporting
The pipeline provides a cleanly decoupled `DataExporter` object used to execute write operations (saving data patches back to your local environment).

```python
from app.workflow import data_exporter, source

my_source = source("odf_fire_occurrence")
exporter = data_exporter()

# Auto-fetches and dumps straight to disk
csv_path = exporter.to_csv(my_source, "data/output/odf_export.csv", limit=5000)

# Or provide your own modified rows
json_path = exporter.to_json(my_source, "data/output/odf_export.json", rows=[{"custom": "row"}])
```

## Example Pipeline

```python
from app.workflow import source, data_exporter

# 1. Bind Source
slido = source("portal_dogami_slido")

# 2. Extract Structural Profile Heuristics
profile = slido.run_meta_analysis("portal_dogami_slido")
print(f"Discovered Columns: {[c['name'] for c in profile['columns']]}")

# 3. Export Output
exporter = data_exporter()
exporter.to_csv(slido, "data/artifacts/slido_patch.csv", limit=100)
```

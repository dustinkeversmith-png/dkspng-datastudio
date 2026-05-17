from app.workflow.source_binding import Source
import json

def metadata_view(source: Source, source_key: str) -> str:
    """Returns a formatted view of the column metadata."""
    if source_key not in source.dataframes:
        return "Source not found."
    
    df = source.dataframes[source_key]
    meta = {
        "key": source_key,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()}
    }
    return json.dumps(meta, indent=2)

def data_view(source: Source, source_key: str, limit: int = 5) -> str:
    """Returns a view of the actual data."""
    if source_key not in source.dataframes:
        return "Source not found."
        
    return source.dataframes[source_key].head(limit).to_string()

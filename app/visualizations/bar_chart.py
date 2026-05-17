from app.workflow.source_binding import Source
import json

def generate_bar_chart(source: Source, source_key: str, x_col: str, y_col: str) -> dict:
    """Generates a relationship map or spec for a bar chart."""
    if source_key not in source.dataframes:
        return {"error": "source key not found"}
        
    df = source.dataframes[source_key]
    
    if x_col not in df.columns or y_col not in df.columns:
         return {"error": "columns missing"}
         
    # Extract top 10 for view
    chart_data = df.head(10)[[x_col, y_col]].to_dict(orient="records")
    
    return {
        "type": "bar_chart",
        "mapping": {"x": x_col, "y": y_col},
        "data": chart_data
    }

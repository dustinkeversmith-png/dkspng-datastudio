from app.workflow.source_binding import Source
import pandas as pd

def run_knn(source: Source, source_key: str, feature_cols: list[str], target_col: str, n_neighbors: int = 3) -> dict:
    """Run KNN clustering/classification using sklearn."""
    if source_key not in source.dataframes:
        return {"error": "source key not found"}
        
    df = source.dataframes[source_key].dropna(subset=feature_cols + [target_col])
    if df.empty:
        return {"error": "no data"}
        
    try:
        from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
        from sklearn.utils.multiclass import type_of_target
        X = df[feature_cols]
        y = df[target_col]
        
        y_type = type_of_target(y)
        if y_type == "continuous":
            model = KNeighborsRegressor(n_neighbors=n_neighbors).fit(X, y)
            return {"status": "success", "n_neighbors": n_neighbors, "model_type": "regressor"}
        else:
            model = KNeighborsClassifier(n_neighbors=n_neighbors).fit(X, y)
            return {"status": "success", "n_neighbors": n_neighbors, "classes": list(model.classes_)}
    except ImportError:
        return {"error": "sklearn not available, KNN mocked"}

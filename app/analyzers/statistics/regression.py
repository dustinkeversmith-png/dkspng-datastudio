from app.workflow.source_binding import Source
import pandas as pd

def run_regression(source: Source, source_key: str, feature_cols: list[str], target_col: str) -> dict:
    """Run a simple linear regression using scikit-learn or scipy fallback."""
    if source_key not in source.dataframes:
        return {"error": "source key not found"}
        
    df = source.dataframes[source_key].dropna(subset=feature_cols + [target_col])
    if df.empty:
        return {"error": "no data after dropping nans"}
        
    try:
        from sklearn.linear_model import LinearRegression
        X = df[feature_cols]
        y = df[target_col]
        model = LinearRegression().fit(X, y)
        return {
            "coefficients": dict(zip(feature_cols, model.coef_)),
            "intercept": float(model.intercept_),
            "r2_score": float(model.score(X, y))
        }
    except ImportError:
        # Fallback to simple correlation if no sklearn
        corrs = {col: df[col].corr(df[target_col]) for col in feature_cols}
        return {"correlations_fallback": corrs}

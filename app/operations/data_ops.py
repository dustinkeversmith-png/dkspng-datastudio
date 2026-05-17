from app.workflow.source_binding import Source
import pandas as pd

def add_calculated_column(source: Source, source_key: str, output_col: str, expression: str, _condition: str = None):
    """Mutate by evaluating an expression and storing in a new column."""
    import re
    pattern = r"(\w+)\[[\'\"]([^\'\"]+)[\'\"]\]"
    
    # Check if either has cross-source references
    matches = re.findall(pattern, expression)
    if _condition:
        matches.extend(re.findall(pattern, _condition))
        
    if matches:
        # Cross-source evaluation
        cross_df = pd.DataFrame()
        unique_matches = list(dict.fromkeys(matches))
        for s_key, c_name in unique_matches:
            if s_key in source.dataframes and c_name in source.dataframes[s_key].columns:
                cross_df[f"{s_key}_{c_name}"] = source.dataframes[s_key][c_name].reset_index(drop=True)
                
        # Rewrite expression and condition
        rewritten_expr = re.sub(pattern, r"\1_\2", expression)
        
        try:
            if cross_df.empty:
                # Fallback to direct Python evaluation or padding if no dfs present
                try:
                    scalar_val = eval(expression)
                except Exception:
                    scalar_val = expression
                result_series = pd.Series([scalar_val] * len(source.dataframes.get(source_key, [])))
            else:
                try:
                    result_series = cross_df.eval(rewritten_expr)
                except Exception:
                    # Treat rewritten_expr as a direct python literal/eval
                    try:
                        scalar_val = eval(rewritten_expr)
                    except Exception:
                        scalar_val = rewritten_expr
                    result_series = pd.Series([scalar_val] * len(cross_df))
                
                if not isinstance(result_series, pd.Series):
                    result_series = pd.Series([result_series] * len(cross_df))
            
            if _condition:
                rewritten_cond = re.sub(pattern, r"\1_\2", _condition)
                mask = cross_df.eval(rewritten_cond)
                if not isinstance(mask, pd.Series):
                    mask = pd.Series([mask] * len(cross_df))
                
            if source_key in source.dataframes:
                df = source.dataframes[source_key]
                # Ensure length matches
                if len(result_series) > len(df):
                    result_series = result_series.iloc[:len(df)]
                elif len(result_series) < len(df):
                    import numpy as np
                    pad = pd.Series([np.nan] * (len(df) - len(result_series)))
                    result_series = pd.concat([result_series, pad], ignore_index=True)
                    
                result_series.index = df.index
                
                if _condition:
                    if output_col not in df.columns:
                        df[output_col] = None
                    mask_vals = mask.values[:len(df)]
                    df.loc[mask_vals, output_col] = result_series[mask_vals]
                else:
                    df[output_col] = result_series
        except Exception as e:
            raise ValueError(f"Failed to evaluate cross-source expression: {e}")
    else:
        # Normal single-source evaluation
        if source_key in source.dataframes:
            df = source.dataframes[source_key]
            try:
                res = df.eval(expression)
                if not isinstance(res, pd.Series):
                    res = pd.Series([res] * len(df), index=df.index)
                if _condition:
                    mask = df.eval(_condition)
                    if output_col not in df.columns:
                        df[output_col] = None
                    df.loc[mask, output_col] = res[mask]
                else:
                    df[output_col] = res
            except Exception as e:
                # If df.eval fails, check if we can evaluate it natively as a Python expression/literal
                try:
                    scalar_val = eval(expression)
                except Exception:
                    scalar_val = expression
                res = pd.Series([scalar_val] * len(df), index=df.index)
                if _condition:
                    try:
                        mask = df.eval(_condition)
                    except Exception:
                        mask = pd.Series([True] * len(df), index=df.index)
                    if output_col not in df.columns:
                        df[output_col] = None
                    df.loc[mask, output_col] = res[mask]
                else:
                    df[output_col] = res

def remove_columns(source: Source, source_key: str, columns: list[str]):
    """Remove specific columns."""
    if source_key in source.dataframes:
        df = source.dataframes[source_key]
        valid_cols = [c for c in columns if c in df.columns]
        source.dataframes[source_key] = df.drop(columns=valid_cols)

def filter_rows(source: Source, source_key: str, query: str):
    """Filter rows using pandas query."""
    if source_key in source.dataframes:
        df = source.dataframes[source_key]
        try:
            source.dataframes[source_key] = df.query(query)
        except Exception as e:
            raise ValueError(f"Failed to query rows: {e}")

def check_base_types(source: Source, source_key: str) -> dict:
    """Tool to check for columns with spatial or time type indicators."""
    types = {}
    if source_key in source.dataframes:
        df = source.dataframes[source_key]
        for col in df.columns:
            l_col = col.lower()
            if "date" in l_col or "time" in l_col:
                types[col] = "time"
            elif "lat" in l_col or "lon" in l_col or "y" == l_col or "x" == l_col:
                types[col] = "spatial"
            elif pd.api.types.is_numeric_dtype(df[col]):
                types[col] = "numeric"
            else:
                types[col] = "categorical"
    return types

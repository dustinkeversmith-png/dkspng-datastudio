"""Expression evaluator for s.add() column expressions.

Supported syntax in expression strings:
    mean(src[col])      aggregate then broadcast
    stdev(src[col])
    sum(src[col])
    min(src[col])
    max(src[col])
    src[col]            raw cross-source column reference
    * / + -             standard arithmetic
    numeric literals
"""
from __future__ import annotations
import re
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.workflow.source_binding import Source


_FUNC_PATTERN = re.compile(r"(mean|stdev|sum|min|max)\((\w+)\[(\w+)\]\)")
_COL_PATTERN = re.compile(r"(\w+)\[(\w+)\]")


def eval_expression(expr: str, source: "Source", output_len: int) -> pd.Series:
    """Evaluate an expression string against a Source's dataframes.

    Steps:
      1. Replace aggregate calls like mean(fire[acres_burned]) → scalar
      2. Replace column refs like fire[acres_burned] → series var
      3. pandas.eval() the rewritten expression
    """
    working_df = pd.DataFrame()
    substitutions: dict[str, str] = {}

    # --- Step 1: aggregate functions ---
    def replace_agg(m: re.Match) -> str:
        func, src_key, col = m.group(1), m.group(2), m.group(3)
        var_name = f"_agg_{func}_{src_key}_{col}"
        if src_key in source.dataframes and col in source.dataframes[src_key].columns:
            series = source.dataframes[src_key][col].dropna()
            agg_map = {
                "mean": series.mean,
                "stdev": series.std,
                "sum": series.sum,
                "min": series.min,
                "max": series.max,
            }
            scalar = agg_map[func]()
            working_df[var_name] = pd.Series([scalar] * output_len)
        return var_name

    expr_rewritten = _FUNC_PATTERN.sub(replace_agg, expr)

    # --- Step 2: raw column references ---
    def replace_col(m: re.Match) -> str:
        src_key, col = m.group(1), m.group(2)
        # Skip if already a known var (from step 1)
        if f"_agg_" in src_key:
            return m.group(0)
        var_name = f"_{src_key}_{col}"
        if src_key in source.dataframes and col in source.dataframes[src_key].columns:
            series = source.dataframes[src_key][col].reset_index(drop=True)
            # Align length
            if len(series) > output_len:
                series = series.iloc[:output_len]
            elif len(series) < output_len:
                import numpy as np
                pad = pd.Series([np.nan] * (output_len - len(series)))
                series = pd.concat([series, pad], ignore_index=True)
            working_df[var_name] = series.values
        return var_name

    expr_rewritten = _COL_PATTERN.sub(replace_col, expr_rewritten)

    # --- Step 3: evaluate ---
    try:
        if working_df.empty:
            # Pure arithmetic / literal
            scalar = eval(expr_rewritten)  # noqa: S307
            return pd.Series([scalar] * output_len)

        result = working_df.eval(expr_rewritten)
        if not isinstance(result, pd.Series):
            result = pd.Series([result] * output_len)
        return result.reset_index(drop=True)
    except Exception as exc:
        raise ValueError(f"Failed to evaluate expression {expr!r}: {exc}") from exc

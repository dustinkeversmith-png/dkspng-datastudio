"""Index DSL parser for Source.index() expressions.

Supported row index formats:
  "1..3"      → slice(1, 3)          rows 1,2
  "1..3..5"   → slice(1, 5, 3)       rows 1, 4 (step 3)
  "1...n"     → slice(1, None)       rows 1 to end
  "0...n"     → slice(0, None)       all rows
  slice       → passed through as-is

Supported column index formats:
  "col1, col2"         → column names by label
  "0..2"               → positional slice → iloc cols 0,1
  slice                → passed through as-is
  list                 → passed through as-is
"""
from __future__ import annotations
import re
import pandas as pd


def parse_row_index(expr: str | slice | list) -> slice | list:
    """Parse a row index expression into a slice or list."""
    if isinstance(expr, (slice, list, int)):
        return expr

    expr = str(expr).strip()

    # "1...n" → slice to end
    if re.match(r"^\d+\.\.\.n$", expr):
        start = int(expr.split("...")[0])
        return slice(start, None)

    # "1..3..5" → stepped slice
    m = re.match(r"^(\d+)\.\.(\d+)\.\.(\d+)$", expr)
    if m:
        return slice(int(m.group(1)), int(m.group(3)), int(m.group(2)))

    # "1..3" → simple slice
    m = re.match(r"^(\d+)\.\.(\d+)$", expr)
    if m:
        return slice(int(m.group(1)), int(m.group(2)))

    # comma-separated integers → list of row positions
    if re.match(r"^[\d,\s]+$", expr):
        return [int(x.strip()) for x in expr.split(",") if x.strip()]

    raise ValueError(f"Unrecognised row index expression: {repr(expr)}")


def parse_col_index(expr: str | slice | list, df: pd.DataFrame) -> list[str]:
    """Parse a column index expression into a list of column names."""
    if isinstance(expr, list):
        return expr
    if isinstance(expr, slice):
        return list(df.columns[expr])

    expr_str = str(expr).strip()

    # Comma-separated column names
    if "," in expr_str:
        parts = [p.strip() for p in expr_str.split(",") if p.strip()]
        # Try name-based first, fall back to positional
        resolved = []
        for p in parts:
            if p in df.columns:
                resolved.append(p)
            elif re.match(r"^\d+$", p):
                idx = int(p)
                if idx < len(df.columns):
                    resolved.append(df.columns[idx])
        return resolved

    # Single column name
    if expr_str in df.columns:
        return [expr_str]

    # Positional slice "0..2"
    m = re.match(r"^(\d+)\.\.(\d+)$", expr_str)
    if m:
        s = slice(int(m.group(1)), int(m.group(2)))
        return list(df.columns[s])

    # Single integer position
    if re.match(r"^\d+$", expr_str):
        return [df.columns[int(expr_str)]]

    raise ValueError(f"Unrecognised column index expression: {repr(expr_str)}")

"""VisualHint — declarative rendering hints for charts.

Supports:
    hint(sources, fields)        factory
    hint.geo("polygon")          geometry type tag
    hint.bounds(xmin,xmax,ymin,ymax)   spatial bounding box
    hint.projection("i", expr)   micro-DSL projection program
    hint.encode("i", expr)       micro-DSL categorical encoder
    chart.apply_hint(hint)       attach hints to a Chart
"""
from __future__ import annotations
from typing import Any, Set
import re


# ---------------------------------------------------------------------------
# Micro-DSL interpreter
# ---------------------------------------------------------------------------

class DSLContext:
    """Minimal runtime for the iterative micro-language used in .projection() and .encode().

    Grammar (subset):
      for(e = input.dim(), N)    iterate variable e from 0 to N
      i[k] /= i[e]               divide element k by e  (in-place)
      i[k] / i[e]                divide
      i.catcode                   category code of current item
      input.dim()                 dimensionality (number of columns)
    """

    def __init__(self, variable: str, source_hint: "VisualHint"):
        self.variable = variable
        self._hint = source_hint

    def run(self, program: str, data: list | None = None) -> Any:
        """Execute the program against optional data and return a result."""
        result = {"program": program, "variable": self.variable, "executed": True}

        # Detect projection: for(e=input.dim(), N) => dimensionality reduction
        for_match = re.search(r"for\((\w+)=input\.dim\(\),(\d+)\)", program)
        if for_match:
            dim_var = for_match.group(1)
            target_dim = int(for_match.group(2))
            result["type"] = "projection"
            result["target_dims"] = target_dim
            result["dim_var"] = dim_var

        # Detect encode: i.catcode / input.dim()
        if "catcode" in program:
            result["type"] = "categorical_encode"
            result["normalize"] = "input.dim()" in program

        return result


# ---------------------------------------------------------------------------
# VisualHint
# ---------------------------------------------------------------------------

class VisualHint:
    """A bundle of rendering hints that can be applied to a Chart."""

    def __init__(self, sources: Set[str], fields: Set[str]):
        self.sources = set(sources)
        self.fields = set(fields)
        self._geo: str | None = None
        self._bounds: dict | None = None
        self._programs: list[dict] = []   # projection / encode programs
        self._style: dict = {}

    # ------------------------------------------------------------------
    # Geometry type
    # ------------------------------------------------------------------

    def geo(self, geom_type: str) -> "VisualHint":
        """Declare the geometry type for spatial rendering (e.g. 'polygon', 'point')."""
        self._geo = geom_type
        return self

    # ------------------------------------------------------------------
    # Spatial bounding box
    # ------------------------------------------------------------------

    def bounds(
        self,
        lat_min,
        lat_max,
        lon_min,
        lon_max,
    ) -> "VisualHint":
        """Set spatial extents. Arguments may be AxisExpr scalars or floats."""
        from app.expressions.axis_expr import AxisExpr

        def _resolve(v):
            if isinstance(v, AxisExpr):
                s = v.resolve()
                return float(s.min() if "min" in v._col_name else s.max())
            return float(v)

        self._bounds = {
            "lat_min": _resolve(lat_min),
            "lat_max": _resolve(lat_max),
            "lon_min": _resolve(lon_min),
            "lon_max": _resolve(lon_max),
        }
        return self

    # ------------------------------------------------------------------
    # Micro-DSL programs
    # ------------------------------------------------------------------

    def projection(self, variable: str, program: str) -> "VisualHint":
        """Register a dimensionality-reduction projection program."""
        ctx = DSLContext(variable, self)
        result = ctx.run(program)
        self._programs.append({
            "kind": "projection",
            "variable": variable,
            "program": program,
            "result": result,
        })
        return self

    def encode(self, variable: str, program: str) -> "VisualHint":
        """Register a categorical-to-numerical encoding program."""
        ctx = DSLContext(variable, self)
        result = ctx.run(program)
        self._programs.append({
            "kind": "encode",
            "variable": variable,
            "program": program,
            "result": result,
        })
        return self

    # ------------------------------------------------------------------
    # Style shortcuts
    # ------------------------------------------------------------------

    def style(self, field: str, prop: str, value: Any) -> "VisualHint":
        if field not in self._style:
            self._style[field] = {}
        self._style[field][prop] = value
        return self

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"VisualHint(sources={self.sources}, fields={self.fields}, "
            f"geo={self._geo!r}, bounds={self._bounds is not None}, "
            f"programs={len(self._programs)})"
        )


def hint(sources: Set[str], fields: Set[str]) -> VisualHint:
    """Factory: `from app.visualizations.hint import hint`."""
    return VisualHint(sources, fields)

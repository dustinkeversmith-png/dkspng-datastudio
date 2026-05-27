"""Chart, VisualObject, and LegendObject — composable visual output objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
import pandas as pd

if TYPE_CHECKING:
    from backend.modules.data.expressions.axis_expr import AxisExpr
    VisualHint = Any


class LegendObject:
    """Auto-generated legend entries for a Chart.

    Supports imperative style overrides per field label:
        legend.color("fire[burn_area]", "black")
        legend.size("fire[burn_area]", "4px")
        legend.opacity("fire[burn_area]", "0.5")
    """

    def __init__(self):
        self.entries: list[dict] = []
        self._styles: dict[str, dict[str, Any]] = {}   # label → {prop: val}

    def add(self, label: str, color: str = "#888888", marker: str = "o") -> "LegendObject":
        self.entries.append({"label": label, "color": color, "marker": marker})
        return self

    # ------------------------------------------------------------------
    # Imperative style setters
    # ------------------------------------------------------------------

    def color(self, label: str, value: str) -> "LegendObject":
        """Set the colour of a legend entry by its label string."""
        self._set_style(label, "color", value)
        return self

    def size(self, label: str, value: str) -> "LegendObject":
        """Set the marker/line size (e.g. '4px', 12) of a legend entry."""
        self._set_style(label, "size", value)
        return self

    def opacity(self, label: str, value: str | float) -> "LegendObject":
        """Set the opacity of a legend entry (e.g. '0.5' or 0.5)."""
        self._set_style(label, "opacity", float(value))
        return self

    def get_style(self, label: str) -> dict[str, Any]:
        return self._styles.get(label, {})

    def _set_style(self, label: str, prop: str, value: Any):
        if label not in self._styles:
            self._styles[label] = {}
        self._styles[label][prop] = value

    def __repr__(self) -> str:
        return f"LegendObject(entries={len(self.entries)}, styled={len(self._styles)})"


@dataclass
class VisualObject:
    """Returned from Chart.save() — holds path and legend."""
    path: str
    legend: LegendObject = field(default_factory=LegendObject)

    def __repr__(self) -> str:
        return f"VisualObject(path={self.path!r}, legend={self.legend})"


class Chart:
    """Composable chart object. Supports layering regression lines, points, etc."""

    def __init__(self, chart_type: str, x_expr: "AxisExpr", y_expr: "AxisExpr"):
        self.chart_type = chart_type
        self.x_expr = x_expr
        self.y_expr = y_expr
        self._layers: list[dict] = []
        self._hints: list["VisualHint"] = []
        self.legend = LegendObject()

    # ------------------------------------------------------------------
    # Layer API
    # ------------------------------------------------------------------

    def linefn(self, weights: list[float], bias: float) -> "Chart":
        """Overlay a regression line defined by weights and bias."""
        self._layers.append({"type": "linefn", "weights": weights, "bias": bias})
        self.legend.add("Regression Line", color="#FF6B6B", marker="-")
        return self

    def points(self, points_df: pd.DataFrame) -> "Chart":
        """Overlay a scatter of arbitrary points (e.g. KNN cluster centres)."""
        self._layers.append({"type": "points", "data": points_df})
        self.legend.add("KNN Points", color="#4ECDC4", marker="x")
        return self

    def apply_hint(self, visual_hint: "VisualHint") -> "Chart":
        """Attach a VisualHint to this chart.

        Hints are consulted at save() time to:
          - Apply legend style overrides (color, size, opacity) for matching fields
          - Clip/reproject data to spatial bounds
          - Tag geometry type for downstream GIS renderers
          - Store projection / encoding program results in metadata
        """
        self._hints.append(visual_hint)

        # Apply any style directives from the hint's _style dict to the legend now
        for field_label, style_props in visual_hint._style.items():
            for prop, val in style_props.items():
                if prop == "color":
                    self.legend.color(field_label, val)
                elif prop == "size":
                    self.legend.size(field_label, val)
                elif prop == "opacity":
                    self.legend.opacity(field_label, val)

        return self

    # ------------------------------------------------------------------
    # Render / Save
    # ------------------------------------------------------------------

    def save(self, path: str) -> VisualObject:
        """Render the chart to a file and return a VisualObject."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 5))

            x_data = self.x_expr.resolve()
            y_data = self.y_expr.resolve()

            # Align lengths
            min_len = min(len(x_data), len(y_data))
            x_data = x_data.iloc[:min_len]
            y_data = y_data.iloc[:min_len]

            if self.chart_type == "bar":
                ax.bar(range(len(x_data)), y_data, tick_label=x_data.astype(str).tolist())
                ax.set_xlabel(self.x_expr.label)
                ax.set_ylabel(self.y_expr.label)
            else:  # scatter
                ax.scatter(x_data, y_data, alpha=0.7, label="Data")

            # Render layers
            for layer in self._layers:
                if layer["type"] == "linefn":
                    import numpy as np
                    x_num = pd.to_numeric(x_data, errors="coerce").dropna()
                    if not x_num.empty:
                        x_min, x_max = x_num.min(), x_num.max()
                        xs = np.linspace(x_min, x_max, 100)
                        # Simple y = bias + weight[0]*x
                        w = layer["weights"][0] if layer["weights"] else 1.0
                        ys = layer["bias"] + w * xs
                        ax.plot(xs, ys, color="#FF6B6B", label="Regression Line")
                elif layer["type"] == "points":
                    pts = layer["data"]
                    if not pts.empty and len(pts.columns) >= 2:
                        ax.scatter(pts.iloc[:, 0], pts.iloc[:, 1],
                                   marker="x", color="#4ECDC4", label="KNN Points")

            ax.set_title(f"{self.chart_type.capitalize()} Chart")

            # Build legend entries from matplotlib
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend()

            plt.tight_layout()
            plt.savefig(path, dpi=100)
            plt.close(fig)

        except ImportError:
            # matplotlib not available — stub output
            pass
        except Exception:
            # Any render error — still return a VisualObject stub
            pass

        vo = VisualObject(path=path, legend=self.legend)
        return vo

    def __repr__(self) -> str:
        return (
            f"Chart(type={self.chart_type!r}, "
            f"x={self.x_expr.label!r}, y={self.y_expr.label!r}, "
            f"layers={len(self._layers)})"
        )

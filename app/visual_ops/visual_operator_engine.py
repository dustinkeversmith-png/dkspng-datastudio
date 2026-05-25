"""Visual operator engine and operator classes."""
from __future__ import annotations
from typing import Any
from app.visual_ops.descriptor_json import VisualDescriptor


class VisualOperatorEngine:
    """Apply a sequence of operators to produce a VisualDescriptor."""

    def __init__(self, source_key: str, plot_type: str = "scatter") -> None:
        self.source_key = source_key
        self.plot_type = plot_type
        self._operators: list[dict[str, Any]] = []

    def axis(self, x: str, y: str) -> "VisualOperatorEngine":
        self._operators.append({"op": "axis", "x": x, "y": y})
        return self

    def color(self, field: str, hint: str = "category_color") -> "VisualOperatorEngine":
        self._operators.append({"op": "color", "field": field, "hint": hint})
        return self

    def size(self, field: str, range: list[float] | None = None) -> "VisualOperatorEngine":
        op: dict[str, Any] = {"op": "size", "field": field, "hint": "fit_range"}
        if range:
            op["range"] = range
        self._operators.append(op)
        return self

    def cluster_overlay(self, cluster_key: str) -> "VisualOperatorEngine":
        self._operators.append({"op": "cluster_overlay", "cluster_result": cluster_key})
        return self

    def uncertainty_band(self, result_key: str) -> "VisualOperatorEngine":
        self._operators.append({"op": "uncertainty_band", "source": result_key})
        return self

    def model_fit_line(self, result_key: str) -> "VisualOperatorEngine":
        self._operators.append({"op": "model_fit_line", "source": result_key})
        return self

    def legend(self, mode: str = "smart") -> "VisualOperatorEngine":
        self._operators.append({"op": "legend", "mode": mode})
        return self

    def build(self, x_field: str = "longitude", y_field: str = "latitude") -> VisualDescriptor:
        return VisualDescriptor(
            plot_type=self.plot_type,
            data={"source": self.source_key, "x": x_field, "y": y_field},
            operators=list(self._operators),
            metadata={"generated_by": "VisualOperatorEngine"},
        )

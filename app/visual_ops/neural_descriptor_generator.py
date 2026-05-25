"""
NeuralDescriptorGenerator — heuristic (rule-based) visual descriptor generator.

Inspects ModelResult / ClusterResult / SamplingResult and emits an appropriate
VisualDescriptor JSON. Designed to be forward-compatible with a real neural
model that could replace the rule engine.
"""
from __future__ import annotations
from typing import Any

from app.visual_ops.descriptor_json import VisualDescriptor
from app.visual_ops.visual_operator_engine import VisualOperatorEngine


class NeuralDescriptorGenerator:
    """Rule-based descriptor generator for analysis results."""

    def from_model_result(self, result: Any, source_key: str = "") -> VisualDescriptor:
        """Generate a VisualDescriptor from a ModelResult."""
        task = getattr(result, "task_type", "unknown")
        key = getattr(result, "model_key", "model")
        target = getattr(result, "target_field", None) or "value"
        features = getattr(result, "feature_fields", [])
        x = features[0] if features else "feature_0"

        engine = VisualOperatorEngine(source_key or result.source_key, plot_type="scatter")
        engine.axis(x, target)

        if task == "classification":
            engine.color(target, hint="category_color")
        elif task == "regression":
            engine.color(x, hint="gradient")
            engine.uncertainty_band(key)
            engine.model_fit_line(key)
        elif task == "decomposition":
            engine.color("PC1", hint="gradient")
        elif task in ("time_series", "signal"):
            engine.uncertainty_band(key)

        engine.legend("smart")
        desc = engine.build(x_field=x, y_field=target)
        desc.metadata["model_key"] = key
        desc.metadata["task_type"] = task
        return desc

    def from_cluster_result(self, result: Any, source_key: str = "") -> VisualDescriptor:
        """Generate a spatial cluster-map descriptor."""
        key = getattr(result, "cluster_key", "kmeans")
        engine = VisualOperatorEngine(source_key, plot_type="scatter")
        engine.axis("longitude", "latitude")
        engine.color("cluster_label", hint="category_color")
        engine.size("cluster_label", range=[4, 16])
        engine.cluster_overlay(key)
        engine.legend("smart")
        desc = engine.build(x_field="longitude", y_field="latitude")
        desc.metadata["cluster_key"] = key
        desc.metadata["k"] = getattr(result, "k", "?")
        return desc

    def from_sampling_result(self, result: Any, source_key: str = "") -> VisualDescriptor:
        """Generate a CI / uncertainty-band descriptor."""
        target = getattr(result, "target", "value") or "value"
        engine = VisualOperatorEngine(source_key, plot_type="bar")
        engine.axis("source_key", target)
        engine.uncertainty_band("sampling_ci")
        engine.legend("smart")
        desc = engine.build(x_field="source_key", y_field=target)
        desc.metadata["sampling_method"] = getattr(result, "method", "unknown")
        return desc

    def auto(self, obj: Any, source_key: str = "") -> VisualDescriptor:
        """Dispatch based on object type."""
        cls_name = type(obj).__name__
        if "Cluster" in cls_name:
            return self.from_cluster_result(obj, source_key)
        elif "Sampling" in cls_name:
            return self.from_sampling_result(obj, source_key)
        else:
            return self.from_model_result(obj, source_key)

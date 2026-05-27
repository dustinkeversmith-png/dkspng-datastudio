"""Registered clustering model for spatial-temporal KMeans analysis."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult
from backend.modules.analysis.models.clustering.spatial_temporal_model import SpatialTemporalKey, infer_stkey


@dataclass
class ClusterResult:
    """Typed KMeans output kept beside the model that creates it."""

    cluster_key: str
    k: int
    labels: list[int]
    centers: list[list[float]]
    feature_names: list[str]
    inertia: float = 0.0
    silhouette_score: float = 0.0
    cluster_profiles: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_model_result(self, source_key: str) -> ModelResult:
        return ModelResult(
            model_key=ClusterModel.model_key,
            task_type=ClusterModel.task_type,
            source_key=source_key,
            feature_fields=self.feature_names,
            target_field=None,
            metrics={
                "k": self.k,
                "inertia": self.inertia,
                "silhouette_score": self.silhouette_score,
                **self.metrics,
            },
            predictions=self.labels,
            metadata={"cluster_key": self.cluster_key},
            lineage={"centers": self.centers, "cluster_profiles": self.cluster_profiles},
        )


@register_model
class ClusterModel(BaseModel):
    """Fit KMeans clusters over inferred spatial-temporal features."""

    model_key = "cluster_kmeans"
    task_type = "clustering"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        k = int(context.get("k", context.get("n_clusters", 6)))
        st_key = context.get("st_key") or infer_stkey(list(X.columns))
        features = context.get("features") or self._build_feature_list(st_key)

        result = self.kmeans(
            df=X,
            source_key=source_key,
            features=features,
            k=k,
            st_key=st_key,
            scale=bool(context.get("scale", True)),
            random_state=int(context.get("random_state", 42)),
        )
        return result.to_model_result(source_key)

    def predict(self, X: pd.DataFrame, context: dict[str, Any]) -> PredictionResult:
        return PredictionResult(model_key=self.model_key)

    def evaluate(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelEvaluation:
        return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

    def kmeans(
        self,
        df: pd.DataFrame,
        source_key: str,
        features: list[str] | None = None,
        k: int = 6,
        st_key: SpatialTemporalKey | None = None,
        scale: bool = True,
        random_state: int = 42,
    ) -> ClusterResult:
        """Run KMeans clustering over numeric spatial-temporal features."""
        if st_key is None:
            st_key = infer_stkey(list(df.columns))
        if features is None:
            features = self._build_feature_list(st_key)

        X_raw, valid_cols = self._build_matrix(df, features)
        cluster_key = f"kmeans_{k}_{source_key}"

        if not X_raw:
            return ClusterResult(
                cluster_key=cluster_key,
                k=0,
                labels=[],
                centers=[],
                feature_names=valid_cols,
                metrics={"warning": "No valid rows after numeric coercion"},
            )

        if len(X_raw) < k:
            k = max(1, len(X_raw))

        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score
            from sklearn.preprocessing import StandardScaler
            import numpy as np

            X_np = np.array(X_raw)
            X_scaled = StandardScaler().fit_transform(X_np) if scale else X_np
            km = KMeans(n_clusters=k, random_state=random_state, n_init="auto")
            labels = km.fit_predict(X_scaled).tolist()
            centers = km.cluster_centers_.tolist()
            inertia = float(km.inertia_)
            sil = 0.0
            if k > 1 and len(set(labels)) > 1:
                try:
                    sil = float(silhouette_score(X_scaled, labels))
                except Exception:
                    pass
        except ImportError:
            labels, centers, inertia = self._mini_kmeans(X_raw, k, random_state)
            sil = 0.0

        profiles = self._build_profiles(X_raw, valid_cols, labels, k)
        size_dist = {str(i): labels.count(i) for i in range(k)}
        return ClusterResult(
            cluster_key=cluster_key,
            k=k,
            labels=labels,
            centers=[[round(v, 6) for v in c] for c in centers],
            feature_names=valid_cols,
            inertia=round(inertia, 4),
            silhouette_score=round(sil, 4),
            cluster_profiles=profiles,
            metrics={"cluster_size_distribution": size_dist},
        )

    @staticmethod
    def _build_feature_list(st_key: SpatialTemporalKey) -> list[str]:
        features = [st_key.latitude_field, st_key.longitude_field]
        if st_key.time_field:
            features.append(st_key.time_field)
        return features

    @staticmethod
    def _build_matrix(df: pd.DataFrame, features: list[str]) -> tuple[list[list[float]] | None, list[str]]:
        valid_cols = [c for c in features if c in df.columns]
        if not valid_cols:
            return None, []

        sub = df[valid_cols].copy()
        for col in valid_cols:
            numeric = pd.to_numeric(sub[col], errors="coerce")
            if numeric.isna().all():
                # Dates are represented as epoch seconds so they can share the numeric matrix.
                try:
                    numeric = pd.to_datetime(sub[col], errors="coerce").astype("int64") / 1e9
                except Exception:
                    pass
            sub[col] = numeric

        sub = sub.dropna(axis=1, how="all").dropna(axis=0, how="any")
        if sub.empty or sub.shape[1] == 0:
            return None, valid_cols
        return sub.values.tolist(), list(sub.columns)

    @staticmethod
    def _build_profiles(X: list[list[float]], cols: list[str], labels: list[int], k: int) -> dict[str, Any]:
        profiles: dict[str, Any] = {}
        from collections import defaultdict

        buckets: dict[int, list[list[float]]] = defaultdict(list)
        for row, label in zip(X, labels):
            buckets[label].append(row)

        for cluster_id in range(k):
            rows = buckets.get(cluster_id, [])
            if not rows:
                profiles[str(cluster_id)] = {"n": 0}
                continue
            n = len(rows)
            means = [sum(r[i] for r in rows) / n for i in range(len(cols))]
            profiles[str(cluster_id)] = {
                "n": n,
                "centroid": {col: round(means[i], 4) for i, col in enumerate(cols)},
            }
        return profiles

    @staticmethod
    def _mini_kmeans(X: list[list[float]], k: int, seed: int) -> tuple[list[int], list[list[float]], float]:
        import math
        import random as _rand

        _rand.seed(seed)
        centers = _rand.sample(X, k)

        def dist(a: list[float], b: list[float]) -> float:
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        labels = [0] * len(X)
        for _ in range(100):
            new_labels = [min(range(k), key=lambda j: dist(row, centers[j])) for row in X]
            if new_labels == labels:
                break
            labels = new_labels
            for j in range(k):
                cluster_pts = [X[i] for i, label in enumerate(labels) if label == j]
                if cluster_pts:
                    n = len(cluster_pts)
                    centers[j] = [sum(p[d] for p in cluster_pts) / n for d in range(len(X[0]))]

        inertia = sum(dist(X[i], centers[labels[i]]) ** 2 for i in range(len(X)))
        return labels, centers, inertia

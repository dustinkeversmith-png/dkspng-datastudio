"""
ClusterEngine — KMeans spatial-temporal clustering.

Builds a normalised feature matrix of [lat, lon, time_norm] and fits
sklearn KMeans.  Falls back to a mini k-means implementation if sklearn
is not available.
"""
from __future__ import annotations

import random
from typing import Any

import pandas as pd

from app.clustering.results import ClusterResult
from app.neighbors.spatial_temporal_distance import SpatialTemporalKey, infer_stkey


class ClusterEngine:
    """Fit KMeans clusters over a DataFrame."""

    def __init__(self, df: pd.DataFrame, source_key: str) -> None:
        self.df = df.copy()
        self.source_key = source_key

    def kmeans(
        self,
        features: list[str] | None = None,
        k: int = 6,
        st_key: SpatialTemporalKey | None = None,
        scale: bool = True,
        random_state: int = 42,
    ) -> ClusterResult:
        """Run KMeans clustering.

        Parameters
        ----------
        features:      Explicit column list.  Auto-inferred from *st_key* if None.
        k:             Number of clusters.
        st_key:        Spatial-temporal key.  Auto-inferred if None.
        scale:         Standardise features before clustering.
        random_state:  Reproducibility seed.
        """
        if st_key is None:
            st_key = infer_stkey(list(self.df.columns))

        if features is None:
            features = [st_key.latitude_field, st_key.longitude_field]
            if st_key.time_field:
                features.append(st_key.time_field)

        X_raw, valid_cols = self._build_matrix(features)
        cluster_key = f"kmeans_{k}_{self.source_key}"

        if not X_raw:
            print(f"  [ClusterEngine] No usable rows after numeric coercion for features={features}")
            return ClusterResult(
                cluster_key=cluster_key, k=0, labels=[], centers=[],
                feature_names=valid_cols,
                metrics={"warning": "No valid rows — check that lat/lon columns exist and are numeric"},
            )

        if len(X_raw) < k:
            k = max(1, len(X_raw))

        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import silhouette_score

            import numpy as np
            X_np = np.array(X_raw)

            if scale:
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X_np)
            else:
                X_scaled = X_np

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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_matrix(self, features: list[str]) -> tuple[list[list[float]] | None, list[str]]:
        """Build a 2D float matrix, converting date strings to epoch seconds."""
        valid_cols = [c for c in features if c in self.df.columns]
        if not valid_cols:
            return None, []
        sub = self.df[valid_cols].copy()
        for col in valid_cols:
            # Try numeric first
            numeric = pd.to_numeric(sub[col], errors="coerce")
            if numeric.isna().all():
                # Try datetime → epoch float
                try:
                    dt = pd.to_datetime(sub[col], errors="coerce")
                    numeric = dt.astype("int64") / 1e9  # seconds since epoch
                except Exception:
                    pass
            sub[col] = numeric
        # Drop columns that are still entirely NaN
        sub = sub.dropna(axis=1, how="all")
        if sub.empty or sub.shape[1] == 0:
            return None, valid_cols
        sub = sub.dropna(axis=0, how="any")
        if sub.empty:
            return None, valid_cols
        return sub.values.tolist(), list(sub.columns)

    @staticmethod
    def _build_profiles(
        X: list[list[float]],
        cols: list[str],
        labels: list[int],
        k: int,
    ) -> dict[str, Any]:
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
    def _mini_kmeans(
        X: list[list[float]],
        k: int,
        seed: int,
    ) -> tuple[list[int], list[list[float]], float]:
        """Minimal k-means without sklearn."""
        import math, random as _rand

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
                cluster_pts = [X[i] for i, l in enumerate(labels) if l == j]
                if cluster_pts:
                    n = len(cluster_pts)
                    centers[j] = [sum(p[d] for p in cluster_pts) / n
                                  for d in range(len(X[0]))]

        inertia = sum(dist(X[i], centers[labels[i]]) ** 2 for i in range(len(X)))
        return labels, centers, inertia

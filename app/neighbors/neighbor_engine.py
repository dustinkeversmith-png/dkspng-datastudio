"""
NeighborEngine — KNN over a spatial-temporal feature matrix.

Builds a feature matrix of [lat_norm, lon_norm, time_norm] and runs
sklearn NearestNeighbors.  Falls back to a pure-Python brute-force
implementation if sklearn is not available.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.neighbors.results import NeighborResult
from app.neighbors.spatial_temporal_distance import SpatialTemporalKey, infer_stkey


class NeighborEngine:
    """Compute K nearest neighbours over a DataFrame."""

    def __init__(self, df: pd.DataFrame, source_key: str) -> None:
        self.df = df.copy()
        self.source_key = source_key

    def knn(
        self,
        features: list[str] | None = None,
        k: int = 5,
        st_key: SpatialTemporalKey | None = None,
    ) -> NeighborResult:
        """Run KNN.

        Parameters
        ----------
        features:   Explicit column list.  If None, uses lat/lon(/time) from *st_key*.
        k:          Number of neighbours.
        st_key:     Spatial-temporal key spec.  Auto-inferred if not given.
        """
        if st_key is None:
            st_key = infer_stkey(list(self.df.columns))

        if features is None:
            features = self._build_feature_list(st_key)

        X, valid_cols = self._build_matrix(features)
        if X is None or len(X) < k + 1:
            return NeighborResult(
                source_key=self.source_key,
                n_neighbors=k,
                feature_fields=valid_cols,
                neighbor_indices=[],
                distances=[],
                metadata={"warning": "Insufficient rows for KNN"},
            )

        k_eff = min(k, len(X) - 1)

        try:
            from sklearn.neighbors import NearestNeighbors
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            nn = NearestNeighbors(n_neighbors=k_eff + 1, metric="euclidean")
            nn.fit(Xs)
            distances_raw, indices_raw = nn.kneighbors(Xs)

            # Strip self (index 0)
            neighbor_indices = [list(map(int, row[1:])) for row in indices_raw]
            distances = [[round(float(d), 4) for d in row[1:]] for row in distances_raw]

        except ImportError:
            # Pure-python brute force fallback
            neighbor_indices, distances = self._brute_force_knn(X, k_eff)

        return NeighborResult(
            source_key=self.source_key,
            n_neighbors=k_eff,
            feature_fields=valid_cols,
            neighbor_indices=neighbor_indices,
            distances=distances,
            metadata={"n_rows": len(X)},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_feature_list(self, st_key: SpatialTemporalKey) -> list[str]:
        features = [st_key.latitude_field, st_key.longitude_field]
        if st_key.time_field:
            features.append(st_key.time_field)
        return features

    def _build_matrix(self, features: list[str]) -> tuple[list[list[float]] | None, list[str]]:
        """Return a numeric 2D list, converting date strings to epoch seconds."""
        valid_cols = [c for c in features if c in self.df.columns]
        if not valid_cols:
            return None, []

        sub = self.df[valid_cols].copy()
        for col in valid_cols:
            numeric = pd.to_numeric(sub[col], errors="coerce")
            if numeric.isna().all():
                try:
                    dt = pd.to_datetime(sub[col], errors="coerce")
                    numeric = dt.astype("int64") / 1e9  # seconds since epoch
                except Exception:
                    pass
            sub[col] = numeric

        # Drop columns that are still entirely NaN, then rows with any NaN
        sub = sub.dropna(axis=1, how="all")
        if sub.empty or sub.shape[1] == 0:
            return None, valid_cols
        sub = sub.dropna(axis=0, how="any")
        if sub.empty:
            return None, valid_cols

        return sub.values.tolist(), list(sub.columns)

    @staticmethod
    def _brute_force_knn(
        X: list[list[float]],
        k: int,
    ) -> tuple[list[list[int]], list[list[float]]]:
        import math

        def dist(a: list[float], b: list[float]) -> float:
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        all_indices: list[list[int]] = []
        all_distances: list[list[float]] = []
        for i, row in enumerate(X):
            dists = [(j, dist(row, X[j])) for j in range(len(X)) if j != i]
            dists.sort(key=lambda t: t[1])
            top = dists[:k]
            all_indices.append([t[0] for t in top])
            all_distances.append([round(t[1], 4) for t in top])

        return all_indices, all_distances

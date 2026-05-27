"""Spatial-temporal helpers and registered nearest-neighbor model."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from backend.modules.analysis.models.base_model import BaseModel, register_model
from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult


@dataclass
class SpatialTemporalKey:
    """Coordinate and optional time fields used to build spatial-temporal matrices."""

    latitude_field: str
    longitude_field: str
    time_field: str | None = None
    crs: str = "EPSG:4326"
    time_grain: str | None = None


@dataclass
class NeighborResult:
    """Typed output from nearest-neighbor spatial-temporal analysis."""

    source_key: str
    n_neighbors: int
    feature_fields: list[str]
    neighbor_indices: list[list[int]]
    distances: list[list[float]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model_result(self) -> ModelResult:
        return ModelResult(
            model_key=NeighborModel.model_key,
            task_type=NeighborModel.task_type,
            source_key=self.source_key,
            feature_fields=self.feature_fields,
            target_field=None,
            metrics={"n_neighbors": self.n_neighbors},
            predictions=self.neighbor_indices,
            metadata={**self.metadata, "distances": self.distances},
        )


@dataclass
class KNNResult:
    """Result of Source.knn()."""

    n_neighbors: int
    model_type: str
    feature_cols: list[str]
    target_col: str
    points: pd.DataFrame = field(default_factory=pd.DataFrame)
    classes: list[Any] = field(default_factory=list)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self) -> str:
        return (
            f"KNNResult(n_neighbors={self.n_neighbors}, "
            f"model_type={self.model_type!r}, classes={self.classes})"
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


def haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    return haversine_km(lat1, lon1, lat2, lon2) * 0.621371


def infer_stkey(columns: list[str]) -> SpatialTemporalKey:
    """Heuristically infer coordinate and time fields from common column names."""
    lat_candidates = ["latitude", "lat", "lat_dd", "LATITUDE", "InitialLatitude", "y"]
    lon_candidates = ["longitude", "lon", "long_dd", "LONGITUDE", "InitialLongitude", "x"]
    time_candidates = ["DATE", "Date", "date", "fireyear", "YEAR", "ign_datetime", "FireDiscoveryDateTime", "year"]

    lat = next((c for c in lat_candidates if c in columns), None)
    lon = next((c for c in lon_candidates if c in columns), None)
    time = next((c for c in time_candidates if c in columns), None)
    return SpatialTemporalKey(latitude_field=lat or "latitude", longitude_field=lon or "longitude", time_field=time)


@register_model
class NeighborModel(BaseModel):
    """Compute K nearest neighbors over inferred spatial-temporal features."""

    model_key = "spatial_temporal_neighbors"
    task_type = "neighbors"

    def fit(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelResult:
        source_key = context.get("source_key", "unknown")
        st_key = context.get("st_key") or infer_stkey(list(X.columns))
        result = self.knn(
            df=X,
            source_key=source_key,
            features=context.get("features"),
            k=int(context.get("k", context.get("n_neighbors", 5))),
            st_key=st_key,
        )
        return result.to_model_result()

    def predict(self, X: pd.DataFrame, context: dict[str, Any]) -> PredictionResult:
        return PredictionResult(model_key=self.model_key)

    def evaluate(self, X: pd.DataFrame, y: pd.Series | None, context: dict[str, Any]) -> ModelEvaluation:
        return ModelEvaluation(model_key=self.model_key, task_type=self.task_type)

    def knn(
        self,
        df: pd.DataFrame,
        source_key: str,
        features: list[str] | None = None,
        k: int = 5,
        st_key: SpatialTemporalKey | None = None,
    ) -> NeighborResult:
        """Run nearest-neighbor analysis on numeric spatial-temporal columns."""
        if st_key is None:
            st_key = infer_stkey(list(df.columns))
        if features is None:
            features = self._build_feature_list(st_key)

        X, valid_cols = self._build_matrix(df, features)
        if X is None or len(X) < k + 1:
            return NeighborResult(
                source_key=source_key,
                n_neighbors=k,
                feature_fields=valid_cols,
                neighbor_indices=[],
                distances=[],
                metadata={"warning": "Insufficient rows for nearest-neighbor analysis"},
            )

        k_eff = min(k, len(X) - 1)
        try:
            from sklearn.neighbors import NearestNeighbors
            from sklearn.preprocessing import StandardScaler

            Xs = StandardScaler().fit_transform(X)
            nn = NearestNeighbors(n_neighbors=k_eff + 1, metric="euclidean")
            nn.fit(Xs)
            distances_raw, indices_raw = nn.kneighbors(Xs)
            neighbor_indices = [list(map(int, row[1:])) for row in indices_raw]
            distances = [[round(float(d), 4) for d in row[1:]] for row in distances_raw]
        except ImportError:
            neighbor_indices, distances = self._brute_force_knn(X, k_eff)

        return NeighborResult(
            source_key=source_key,
            n_neighbors=k_eff,
            feature_fields=valid_cols,
            neighbor_indices=neighbor_indices,
            distances=distances,
            metadata={"n_rows": len(X)},
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
                # Date strings are converted to epoch seconds for distance calculations.
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
    def _brute_force_knn(X: list[list[float]], k: int) -> tuple[list[list[int]], list[list[float]]]:
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

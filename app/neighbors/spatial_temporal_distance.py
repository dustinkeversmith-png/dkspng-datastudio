"""Spatial-temporal distance types and key specification."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SpatialTemporalKey:
    """Describes the coordinate and time fields for a source.

    Used by NeighborEngine and ClusterEngine to build a unified feature
    matrix over (latitude, longitude, normalised_time).
    """
    latitude_field: str
    longitude_field: str
    time_field: str | None = None
    crs: str = "EPSG:4326"
    time_grain: str | None = None  # "day", "month", "year"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    return haversine_km(lat1, lon1, lat2, lon2) * 0.621371


def infer_stkey(columns: list[str]) -> SpatialTemporalKey:
    """Heuristically infer the SpatialTemporalKey from column names."""
    lat_candidates = ["latitude", "lat", "lat_dd", "LATITUDE", "InitialLatitude", "y"]
    lon_candidates = ["longitude", "lon", "long_dd", "LONGITUDE", "InitialLongitude", "x"]
    time_candidates = ["DATE", "Date", "date", "fireyear", "YEAR", "ign_datetime",
                       "FireDiscoveryDateTime", "year"]

    lat = next((c for c in lat_candidates if c in columns), None)
    lon = next((c for c in lon_candidates if c in columns), None)
    time = next((c for c in time_candidates if c in columns), None)

    return SpatialTemporalKey(
        latitude_field=lat or "latitude",
        longitude_field=lon or "longitude",
        time_field=time,
    )

"""Place names → coordinates and human distance strings → kilometers."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Literal

_UserAgent = "RegionalDataStudio/0.7 (local workflow; contact: dev@localhost)"

GENERIC_LATITUDE_COLUMNS = [
    "latitude",
    "lat",
    "y",
    "ycoord",
    "y_coord",
    "point_y",
    "centroid_y",
    "geometry_y",
]
GENERIC_LONGITUDE_COLUMNS = [
    "longitude",
    "lon",
    "lng",
    "long",
    "x",
    "xcoord",
    "x_coord",
    "point_x",
    "centroid_x",
    "geometry_x",
]

_OFFLINE_PLACE_FALLBACKS = {
    "oregon": (43.8041, -120.5542),
    "oregon, or": (43.8041, -120.5542),
    "oregon, usa": (43.8041, -120.5542),
    "oregon, or, usa": (43.8041, -120.5542),
    "portland oregon": (45.5152, -122.6784),
    "portland oregon, or": (45.5152, -122.6784),
    "klamath falls oregon": (42.2249, -121.7817),
    "klamath falls oregon, or": (42.2249, -121.7817),
}


def parse_distance(raw: str | float | int) -> float:
    """
    Convert ``5mi``, ``10km``, or a bare number (interpreted as kilometers) to km.
    """
    if isinstance(raw, (int, float)):
        return float(raw)

    s = str(raw).strip().lower().replace(" ", "")
    m = re.match(r"^([\d.]+)\s*(mi|mile|miles|km|kilometer|kilometers|)$", s)
    if not m:
        raise ValueError(f"Unrecognized distance format: {raw!r}")
    val = float(m.group(1))
    unit = m.group(2)
    if unit in ("mi", "mile", "miles"):
        return val * 1.609344
    return val


def resolve_place_coordinates_nominatim(place: str, *, timeout_s: float = 12.0) -> tuple[float, float]:
    """Forward geocode using OpenStreetMap Nominatim (network)."""
    q = urllib.parse.quote_plus(place.strip())
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": _UserAgent})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        raise ValueError(f"No geocoding results for: {place!r}")
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon


def _fallback_place_coordinates(place: str) -> tuple[float, float] | None:
    normalized = " ".join(place.lower().replace(",", " , ").split()).replace(" ,", ",")
    return _OFFLINE_PLACE_FALLBACKS.get(normalized)


def _extract_coordinate_pair(value: Any) -> tuple[float, float] | None:
    if isinstance(value, dict):
        lat = value.get("latitude", value.get("lat", value.get("y")))
        lon = value.get("longitude", value.get("lon", value.get("lng", value.get("x"))))
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return float(value[0]), float(value[1])
    if isinstance(value, str):
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", value)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None


class GeoQueryResolver:
    """
    Expandable geo resolver: inject a custom ``geocode_fn`` for tests/offline bundles.

    Default uses Nominatim public endpoint (rate-limited; OK for dev).
    """

    def __init__(self, geocode_fn: Callable[[str], tuple[float, float]] | None = None) -> None:
        self._geocode: Callable[[str], tuple[float, float]] = geocode_fn or resolve_place_coordinates_nominatim

    def near(
        self,
        place: str | tuple[float, float] | list[float] | dict[str, Any],
        distance: str | float | int,
        *,
        state: str | None = None,
        country: str | None = None,
        query_type: Literal["auto", "place", "coordinates"] = "auto",
        coordinate_columns: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a near query into a profile patch.

        ``query_type="auto"`` geocodes place-like strings and accepts direct
        coordinate inputs such as ``(lat, lon)``, ``"lat,lon"``, or
        ``{"lat": ..., "lon": ...}``.
        """
        pair = _extract_coordinate_pair(place)
        if query_type == "coordinates" or (query_type == "auto" and pair is not None):
            if pair is None:
                raise ValueError("coordinates near query requires lat/lon values")
            lat, lon = pair
            label = f"{lat},{lon}"
            source = "coordinates"
        else:
            text = str(place).strip()
            parts = [text]
            if state:
                parts.append(state.strip())
            if country:
                parts.append(country.strip())
            query = ", ".join(parts)
            fallback = _fallback_place_coordinates(query) or _fallback_place_coordinates(text)
            if fallback is not None:
                lat, lon = fallback
            else:
                lat, lon = self._geocode(query)
            label = text
            source = "place"
        km = parse_distance(distance)
        columns = coordinate_columns or {
            "latitude": GENERIC_LATITUDE_COLUMNS,
            "longitude": GENERIC_LONGITUDE_COLUMNS,
        }
        out: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "radius_km": km,
            "near_label": label,
            "near_query_type": source,
            "near_format": {
                "kind": "geocoded_point",
                "input": source,
                "requires": ["latitude", "longitude"],
                "coordinate_columns": columns,
                "description": "Datasets without explicit latitude/longitude can map generic coordinate columns or geometry-derived x/y columns.",
            },
            "geo_column_candidates": columns,
        }
        if state:
            out["near_state"] = state.strip()
        if country:
            out["near_country"] = country.strip()
        return out


def resolve_place_coordinates(place: str) -> tuple[float, float]:
    """Module-level default geocoder (Nominatim)."""
    return resolve_place_coordinates_nominatim(place)

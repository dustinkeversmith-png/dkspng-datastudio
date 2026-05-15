"""
GIS-oriented hints (bbox, web-map context) kept on the query profile for exporters/UI.

Does not execute spatial queries by itself — coordinates flow through ``bbox`` / geo filters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GisQueryResolver:
    """
    Build portable GIS metadata blocks (e.g. ArcGIS Hub dataset URLs, CRS notes).

    Example hub page for Oregon wildfire context:
    https://oregon-department-of-forestry-geo.hub.arcgis.com/datasets/e3896b22b0ab41d4835f82574ed81fb0_1/explore
    """

    def hub_context(self, dataset_url: str, *, layer_name: str | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {"gis_hub_dataset_url": dataset_url.strip()}
        if layer_name:
            out["gis_layer_label"] = layer_name
        return out

    def bbox(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict[str, Any]:
        return {"bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}"}

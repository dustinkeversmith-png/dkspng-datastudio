import pandas as pd
import requests
from math import atan, exp, pi

from app.connectors.base import Connector


class ArcGisRestConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        if self.source.source_url.startswith("REPLACE_WITH_"):
            raise ValueError(
                f"{self.source.source_key} has a placeholder source_url. "
                "Replace it with an ArcGIS REST query endpoint before running real ingestion."
            )

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": 5000,
        }

        response = requests.get(self.source.source_url, params=params, timeout=60)
        response.raise_for_status()

        payload = response.json()
        if payload.get("error", {}).get("message") == "Pagination is not supported.":
            params.pop("resultRecordCount", None)
            response = requests.get(self.source.source_url, params=params, timeout=60)
            response.raise_for_status()
            payload = response.json()
        features = payload.get("features", [])
        rows = []

        for feature in features:
            props = feature.get("properties") or feature.get("attributes", {}) or {}
            geometry = feature.get("geometry", {}) or {}
            coordinates = geometry.get("coordinates")

            if geometry.get("type") == "Point" and coordinates:
                props["longitude"] = coordinates[0]
                props["latitude"] = coordinates[1]
            elif "x" in geometry and "y" in geometry:
                x = float(geometry["x"])
                y = float(geometry["y"])
                if abs(x) > 180 or abs(y) > 90:
                    props["longitude"] = x / 20037508.34 * 180
                    props["latitude"] = (180 / pi) * (2 * atan(exp(y / 20037508.34 * pi)) - pi / 2)
                else:
                    props["longitude"] = x
                    props["latitude"] = y

            rows.append(props)

        return pd.DataFrame(rows)

import pandas as pd
from app.connectors.base import Connector


class CsvConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        return pd.read_csv(self.source.source_url)


class ExcelConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        return pd.read_excel(self.source.source_url)


class GeoJsonConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        import geopandas as gpd
        gdf = gpd.read_file(self.source.source_url)
        if "geometry" in gdf:
            gdf["longitude"] = gdf.geometry.centroid.x
            gdf["latitude"] = gdf.geometry.centroid.y
        return pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))

import pandas as pd
from app.connectors.base import Connector


class CsvConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        path = self._ensure_downloaded()
        return pd.read_csv(path)


class ExcelConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        path = self._ensure_downloaded()
        return pd.read_excel(path)


class GeoJsonConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        import geopandas as gpd
        path = self._ensure_downloaded()
        gdf = gpd.read_file(path)
        if "geometry" in gdf:
            gdf["longitude"] = gdf.geometry.centroid.x
            gdf["latitude"] = gdf.geometry.centroid.y
        return pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))


class SqliteConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        import sqlite3
        path = self._ensure_downloaded()
        conn = sqlite3.connect(path)
        
        # Read the first available table
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql(query, conn)
        
        if not tables.empty:
            first_table = tables.iloc[0]['name']
            df = pd.read_sql(f"SELECT * FROM {first_table}", conn)
        else:
            df = pd.DataFrame()
            
        conn.close()
        return df

class WebApiConnector(Connector):
    def fetch(self) -> pd.DataFrame:
        import requests
        headers = {"User-Agent": "RegionalDataStudio/1.0 (local dev)"}
        response = requests.get(self.source.source_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return pd.DataFrame([data])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

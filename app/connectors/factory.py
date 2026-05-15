from app.connectors.arcgis_rest import ArcGisRestConnector
from app.connectors.tabular import CsvConnector, ExcelConnector, GeoJsonConnector, SqliteConnector, WebApiConnector
from app.schemas import SourceDefinition


def create_connector(source: SourceDefinition):
    match source.connector_type:
        case "arcgis_rest":
            return ArcGisRestConnector(source)
        case "csv" | "web":
            return CsvConnector(source)
        case "excel":
            return ExcelConnector(source)
        case "geojson":
            return GeoJsonConnector(source)
        case "sqlite":
            return SqliteConnector(source)
        case "web_api":
            return WebApiConnector(source)
        case _:
            raise ValueError(f"Unsupported connector_type: {source.connector_type}")

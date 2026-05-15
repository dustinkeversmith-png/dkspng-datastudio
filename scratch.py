from app.schemas import SourceDefinition
from app.source_registry import add_or_update_source
from app.workflow import source

add_or_update_source(
    SourceDefinition(
        source_key="portal_dogami_slido",
        display_name="DOGAMI SLIDO (ArcGIS REST)",
        category="natural_disasters",
        connector_type="arcgis_rest",
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
    )
)

slido = source(
    "portal_dogami_slido",
    "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
)

rows = slido.fetch(limit=2)
print("Row 1 keys:", rows[0].keys())
print("Row 1 sample data:", {k: rows[0][k] for k in ["latitude", "longitude", "x", "y", "POINT_X", "POINT_Y", "lat", "lon"] if k in rows[0]})

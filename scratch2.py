import requests

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "geometry": "-124.5,42.0,-122.0,43.5",
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "inSR": "4326",
    "f": "json",
}
response = requests.get("https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query", params=params)
payload = response.json()
print("Total features returned:", len(payload.get("features", [])))

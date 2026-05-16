import re

def discover_metadata(source_key: str, source_url: str, connector_type: str) -> str:
    """Returns the official documentation URL for a given source."""
    if connector_type == "csv" and ("socrata" in source_url.lower() or "data.oregon.gov" in source_url.lower()):
        # e.g., https://data.oregon.gov/resource/fa7z-shhx.csv -> https://data.oregon.gov/api/views/fa7z-shhx.json
        match = re.search(r'(.+)/resource/([a-zA-Z0-9\-]+)\.csv', source_url)
        if match:
            return f"{match.group(1)}/api/views/{match.group(2)}.json"
            
    if connector_type == "arcgis_rest":
        # Removes /query and requests ?f=pjson
        return re.sub(r'/query.*$', '?f=pjson', source_url)
        
    if connector_type == "research_ref" or "figshare" in source_url:
        if "api.figshare.com" in source_url:
            return source_url
        match = re.search(r'doi\.org/(.+)', source_url)
        if match:
             return f"https://api.datacite.org/works/{match.group(1)}"
             
    if "zip" in source_url.lower():
        return source_url + "#metadata_index"

    return source_url

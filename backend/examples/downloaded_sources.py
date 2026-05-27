
from backend.schemas import SourceDefinition
from backend.source_registry import add_or_update_source
from backend.workflow.source_binding import source
from backend.workflow import data_exporter, source

def register_downloaded_sources() -> None:
    """Register external sources that require downloading before querying."""
    # SIT-209 History - ZIP/XLSX download
    add_or_update_source(
        SourceDefinition(
            source_key="sit_209_history",
            display_name="SIT-209 History",
            category="Public Download",
            connector_type="excel", # Will attempt to use ExcelConnector
            source_url="https://wildfireweb-prod-media-bucket.s3.us-gov-west-1.amazonaws.com/s3fs-public/2025-06/18_2_SIT209_HISTORY_INCIDENT_209_REPORTS.xlsx",
            requires_download=True,
            notes="Direct ZIP/XLSX download"
        )
    )


def demonstrate_downloaded_sources() -> None:
    """Demonstrate how downloaded sources are processed.
    
    Note: The provided URLs are landing pages, not direct file links.
    In a real scenario with direct links to .xlsx or .sqlite files,
    this fetch() call will download the file to the local disk first,
    and then parse the data into a DataFrame.
    """
    print("Registering sources...")
    register_downloaded_sources()


    sit_209 = source("sit_209_history")


    try:
        rows2 = sit_209.fetch(limit=5000)
        print(f"Retrieved {len(rows2)} records. Exporting...")
        exporter = data_exporter()
        csv_path2 = "data/sit_209_history.csv"
        exporter.to_csv(sit_209, csv_path2, rows=rows2)
    except Exception as e:
        print(f"Could not parse sit_209_history (expected since URL is a landing page): {e}")

    # We fetch the definition to print out the properties
    from backend.source_registry import get_source
    sit_209_def = get_source(sit_209.key)

    print(f"Source: {sit_209.key}")
    print(f"Requires Download: {sit_209_def.requires_download}")
    print(f"Connector Type: {sit_209_def.connector_type}")
    
    print("-" * 30)

if __name__ == "__main__":
    demonstrate_downloaded_sources()

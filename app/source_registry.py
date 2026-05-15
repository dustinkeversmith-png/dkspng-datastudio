from app.schemas import SourceDefinition

SOURCES: dict[str, SourceDefinition] = {
    "odf_fire_occurrence": SourceDefinition(
        source_key="odf_fire_occurrence",
        display_name="ODF Fire Occurrence 2000-2025",
        category="natural_disasters",
        connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=50000",
        notes="Oregon Dept of Forestry wildfire occurrence data by point of origin.",
    ),
    "slido_landslide_registry_sample": SourceDefinition(
        source_key="slido_landslide_registry_sample",
        display_name="DOGAMI SLIDO Landslide Inventory",
        category="natural_disasters",
        connector_type="arcgis_rest",
        source_url="REPLACE_WITH_SLIDO_ARCGIS_REST_QUERY_ENDPOINT",
        notes="DOGAMI SLIDO landslide source. Replace with the service/layer query endpoint.",
    ),
    "dogami_slido_landslides": SourceDefinition(
        source_key="dogami_slido_landslides",
        display_name="DOGAMI SLIDO Historic Landslide Points",
        category="natural_disasters",
        connector_type="arcgis_rest",
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
        notes="DOGAMI SLIDO historic landslide point records.",
    ),
    "generic_csv_sample": SourceDefinition(
        source_key="generic_csv_sample",
        display_name="[DEV ONLY] Generic Regional CSV",
        category="dev_sample",
        connector_type="csv",
        source_url="./data/examples/generic_observations.csv",
        notes="Only for local testing. Do not use for real comparisons.",
    ),
    # --- Portal demos (see ``app.examples.three_portal_bindings.PORTAL_APIS``) ---
    "portal_odf_firestats": SourceDefinition(
        source_key="portal_odf_firestats",
        display_name="ODF Fire Statistics (data.oregon.gov API)",
        category="natural_disasters",
        connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv?$limit=50000",
        notes=(
            "Landing https://www.oregon.gov/odf/fire/pages/firestats.aspx — "
            "Socrata data endpoint fa7z-shhx (CSV/JSON via data.oregon.gov)."
        ),
    ),
    "portal_dogami_slido": SourceDefinition(
        source_key="portal_dogami_slido",
        display_name="DOGAMI SLIDO (ArcGIS REST query)",
        category="natural_disasters",
        connector_type="arcgis_rest",
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
        notes=(
            "Landing https://www.oregon.gov/dogami/slido/pages/index.aspx — "
            "MapServer query endpoint for layer 0."
        ),
    ),
    "portal_sci_data_ics209_demo": SourceDefinition(
        source_key="portal_sci_data_ics209_demo",
        display_name="Sci Data 2023 ICS-209-PLUS (CSV demo surrogate)",
        category="research_reference",
        connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=8000",
        notes=(
            "Article https://doi.org/10.1038/s41597-023-01955-0 — "
            "Figshare archives https://doi.org/10.6084/m9.figshare.19858927 ; "
            "metadata API https://api.figshare.com/v2/articles/19858927 . "
            "Uses Oregon CSV as a small ingestible surrogate; swap for CSV extracted from Figshare ZIPs."
        ),
    ),
}


def get_source(source_key: str) -> SourceDefinition:
    try:
        return SOURCES[source_key]
    except KeyError as exc:
        raise KeyError(f"Unknown source_key: {source_key}") from exc


def list_sources() -> list[SourceDefinition]:
    return list(SOURCES.values())


def add_or_update_source(source: SourceDefinition) -> SourceDefinition:
    """Register a new source or overwrite an existing source key."""
    SOURCES[source.source_key] = source
    return source


def delete_source(source_key: str) -> None:
    if source_key not in SOURCES:
        raise KeyError(f"Unknown source_key: {source_key}")
    del SOURCES[source_key]

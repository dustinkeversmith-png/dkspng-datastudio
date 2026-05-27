"""
Bindings + runnable demo for three public portals:

1. Oregon ODF fire statistics -> data.oregon.gov Socrata API (CSV / SoQL).
2. DOGAMI SLIDO landslides -> ArcGIS REST MapServer query endpoint.
3. St Denis et al., Sci Data 2023 (ICS-209-PLUS) -> Figshare dataset DOI + API; CSV demo uses Oregon open data as a lightweight tabular surrogate for ingestion.

Run (from repo root, PYTHONPATH=.): python -m app.examples.three_portal_bindings
"""

from __future__ import annotations

from backend.schemas import SourceDefinition
from backend.source_registry import add_or_update_source
from backend.workflow import analysis_tools, bind_sources, charts, source


PORTAL_APIS = {
    "odf_firestats": {
        "landing_page": "https://www.oregon.gov/odf/fire/pages/firestats.aspx",
        "open_data_csv": "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=50000",
        "open_data_json": "https://data.oregon.gov/resource/fa7z-shhx.json?%24limit=5000",
        "socrata_dataset": "https://data.oregon.gov/Natural-Resources/ODF-Fire-Occurrence-Data-2000-2022/fbwv-q84y",
    },
    "dogami_slido": {
        "landing_page": "https://www.oregon.gov/dogami/slido/pages/index.aspx",
        "arcgis_mapserver": "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer",
        "arcgis_layer_query": (
            "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query"
            "?where=1%3D1&outFields=*&returnGeometry=true&f=json"
        ),
    },
    "sci_data_ics209": {
        "article": "https://www.nature.com/articles/s41597-023-01955-0",
        "doi": "https://doi.org/10.1038/s41597-023-01955-0",
        "figshare_dataset": "https://doi.org/10.6084/m9.figshare.19858927",
        "figshare_api": "https://api.figshare.com/v2/articles/19858927",
        "csv_demo_surrogate": "https://data.oregon.gov/resource/fa7z-shhx.csv?%24limit=8000",
    },
}


def register_three_portal_sources() -> None:
    """Upsert registry entries pointing at live APIs / documented fallbacks."""
    add_or_update_source(
        SourceDefinition(
            source_key="portal_odf_firestats",
            display_name="ODF Fire Statistics (data.oregon.gov)",
            category="natural_disasters",
            connector_type="csv",
            source_url=PORTAL_APIS["odf_firestats"]["open_data_csv"],
            notes=(
                "Landing: https://www.oregon.gov/odf/fire/pages/firestats.aspx - "
                "tabular API via Socrata (resource fbwv-q84y)."
            ),
        )
    )
    add_or_update_source(
        SourceDefinition(
            source_key="portal_dogami_slido",
            display_name="DOGAMI SLIDO (ArcGIS REST)",
            category="natural_disasters",
            connector_type="arcgis_rest",
            source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
            notes=(
                "Landing: https://www.oregon.gov/dogami/slido/pages/index.aspx - "
                "query layer 0 on SLIDO42 MapServer."
            ),
        )
    )
    add_or_update_source(
        SourceDefinition(
            source_key="portal_sci_data_ics209_demo",
            display_name="ICS-209-PLUS / Sci Data 2023 (CSV demo surrogate)",
            category="research_reference",
            connector_type="csv",
            source_url=PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"],
            notes=(
                "Article https://doi.org/10.1038/s41597-023-01955-0 - "
                "full ICS-209-PLUS archives: Figshare https://doi.org/10.6084/m9.figshare.19858927 "
                "(ZIP bundles). Figshare metadata JSON: https://api.figshare.com/v2/articles/19858927 . "
                "This key uses Oregon ODF CSV as a small tabular surrogate for connector demos."
            ),
        )
    )


def demo_session_charts() -> None:
    """Wire a session with automatic geo + foreach/grid/range chart generators."""
    register_three_portal_sources()

    odf = source("portal_odf_firestats", PORTAL_APIS["odf_firestats"]["open_data_csv"])
    slido = source(
        "portal_dogami_slido",
        "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
    )
    ics = source("portal_sci_data_ics209_demo", PORTAL_APIS["sci_data_ics209"]["csv_demo_surrogate"])

    combined = bind_sources(odf, slido, ics)
    chart = charts()
    tools = analysis_tools()

    odf.near("Oregon", "200km", state="OR", country="USA", query_type="place").between("year", 2005, 2020)
    slido.near(
        {"lat": 43.8041, "lon": -120.5542},
        "200km",
        query_type="coordinates",
        coordinate_columns={"latitude": ["y", "POINT_Y"], "longitude": ["x", "POINT_X"]},
    )
    ics.near("43.8041,-120.5542", "200km").between("metric_value", 0, 1000000)

    chart.foreach(odf, "year", "metric_value", "latitude", "longitude", name_prefix="odf_grid", kind="scatter,bar")
    chart.foreach_expand(ics, "year", "metric_value", "metric_value", "year", kinds=("scatter", "bar"), name_prefix="ics_grid")
    chart.foreach_ranges(odf, "year", "metric_value", [(2008, 2012), (2013, 2018)], base_name="odf_win")

    chart.metric(
        combined,
        "cross_odf_ics",
        [
            {
                "source_key": "portal_odf_firestats",
                "x": "year",
                "y": "metric_value",
                "label": "ODF",
                "style": {"color": "#c0392b"},
            },
            {
                "source_key": "portal_sci_data_ics209_demo",
                "x": "year",
                "y": "metric_value",
                "label": "Demo surrogate",
                "style": {"color": "#2980b9"},
            },
        ],
        layout={"title": {"text": "Fire metrics - dual feed"}},
        save_path="artifacts/charts/function_outputs/cross_odf_ics.svg",
    )

    chart.metric(
        combined,
        "styled_pair",
        [
            {
                "source_key": "portal_odf_firestats",
                "x": "year",
                "y": "metric_value",
                "label": "ODF",
                "style": {"color": "#e67e22"},
            },
            {
                "source_key": "portal_sci_data_ics209_demo",
                "x": "year",
                "y": "metric_value",
                "label": "Demo surrogate",
                "style": {"color": "#27ae60"},
            },
        ],
        layout={"legend": {"orientation": "h"}},
    )

    print("sources", combined.minor_source_keys)
    print("charts", len(chart.definitions))
    print("sample chart types", [c.get("type") for c in chart.definitions[:8]])
    try:
        rows = combined.fetch(source_keys=["portal_odf_firestats", "portal_sci_data_ics209_demo"], limit=8, print_rows=True)
        print("row count", len(rows))
        print("correlation", tools.correlation(rows, variables=["year", "metric_value"]))
    except Exception as exc:
        print("direct data fetch skipped:", exc)


if __name__ == "__main__":
    demo_session_charts()

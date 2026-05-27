"""
Project 3 — Geo-Spatial Intersection & Land Coverage Map
=========================================================

Loads all registered regional sources, extracts spatial point clouds,
computes convex-hull footprints and their pairwise intersections, then
renders two outputs:

  1. data/plots/project3/intersection_map.html  — interactive Folium map
     with OpenStreetMap + Stamen Terrain tile layers, per-source data
     points, convex-hull polygons, and shaded intersection regions.

  2. data/plots/project3/intersection_static.png — static matplotlib
     figure with a contextily tile basemap.

Run from repo root:
    python project_3.py
"""
from __future__ import annotations

import json
import math
import os
import warnings
from typing import Any

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CENTRE_LAT = 42.2249   # Klamath Falls, OR
CENTRE_LON = -121.7817
QUERY_RADIUS_MI = 50
PLOT_DIR = os.path.join("data", "plots", "project3")

# Date column candidates per source (for temporal intersection)
DATE_COLS: dict[str, list[str]] = {
    "noaa_gsod":               ["DATE", "date"],
    "epa_air_quality":         ["Date", "date", "DATE"],
    "portal_odf_firestats":    ["reportdate", "fireyear", "date", "DATE"],
    "portal_dogami_slido":     ["Event_Date", "eventdate", "date"],
    "nifc_wildfire_incidents": ["FireDiscoveryDateTime", "ContainmentDateTime", "date"],
    "portal_sci_data_ics209_demo": ["reportdate", "date", "DATE"],
}

# Per-source display config
SOURCE_CONFIG: dict[str, dict] = {
    "noaa_gsod": {
        "display": "NOAA Daily Weather",
        "color":   "#2196F3",   # blue
        "lat_candidates": ["LATITUDE", "latitude", "lat"],
        "lon_candidates": ["LONGITUDE", "longitude", "lon"],
    },
    "epa_air_quality": {
        "display": "EPA Air Quality Index",
        "color":   "#4CAF50",   # green — county centroid fallback
        "lat_candidates": ["latitude", "lat", "Latitude"],
        "lon_candidates": ["longitude", "lon", "Longitude"],
    },
    "portal_odf_firestats": {
        "display": "ODF Fire Statistics",
        "color":   "#FF9800",   # orange
        "lat_candidates": ["lat_dd", "latitude", "lat", "Latitude"],
        "lon_candidates": ["long_dd", "longitude", "lon", "Longitude"],
    },
    "portal_dogami_slido": {
        "display": "DOGAMI Landslide Database",
        "color":   "#F44336",   # red
        "lat_candidates": ["latitude", "lat", "lat_dd", "LATITUDE"],
        "lon_candidates": ["longitude", "lon", "long_dd", "LONGITUDE"],
    },
    "nifc_wildfire_incidents": {
        "display": "NIFC Wildfire Incidents",
        "color":   "#9C27B0",   # purple
        "lat_candidates": ["latitude", "lat", "Latitude", "LATITUDE"],
        "lon_candidates": ["longitude", "lon", "Longitude", "LONGITUDE"],
    },
    "portal_sci_data_ics209_demo": {
        "display": "ICS-209 Fire Reports",
        "color":   "#FF5722",   # deep orange
        "lat_candidates": ["lat_dd", "latitude", "lat"],
        "lon_candidates": ["long_dd", "longitude", "lon"],
    },
}

# Oregon county centroids for EPA (no point-level coords)
OREGON_COUNTY_CENTROIDS: dict[str, tuple[float, float]] = {
    "Klamath":   (42.59, -121.73),
    "Jackson":   (42.43, -122.72),
    "Josephine": (42.35, -123.55),
    "Douglas":   (43.28, -123.12),
    "Lane":      (43.94, -122.07),
    "Deschutes": (43.93, -121.22),
    "Lake":      (42.80, -120.35),
}

# ---------------------------------------------------------------------------
# Source registration (mirrors project_2)
# ---------------------------------------------------------------------------

from backend.schemas import SourceDefinition
from backend.source_registry import add_or_update_source, get_source
from backend.workflow.source_binding import source as make_source


def register_sources() -> None:
    add_or_update_source(SourceDefinition(
        source_key="nifc_wildfire_incidents",
        display_name="NIFC Wildfire Incidents (ArcGIS REST)",
        category="natural_hazards", connector_type="arcgis_rest",
        source_url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations/FeatureServer/0/query",
    ))
    add_or_update_source(SourceDefinition(
        source_key="noaa_gsod",
        display_name="NOAA Global Surface Summary (CSV)",
        category="weather", connector_type="csv",
        source_url="https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2023/72219013874.csv",
        requires_download=True,
    ))
    add_or_update_source(SourceDefinition(
        source_key="epa_air_quality",
        display_name="EPA AQS Daily AQI by County 2023",
        category="environmental", connector_type="csv",
        source_url="https://aqs.epa.gov/aqsweb/airdata/daily_aqi_by_county_2023.zip",
        requires_download=True,
    ))
    add_or_update_source(SourceDefinition(
        source_key="portal_odf_firestats",
        display_name="ODF Fire Statistics",
        category="natural_disasters", connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv",
        latitude_fields=["lat_dd", "latitude", "lat"],
        longitude_fields=["long_dd", "longitude", "lon"],
    ))
    add_or_update_source(SourceDefinition(
        source_key="portal_dogami_slido",
        display_name="DOGAMI SLIDO (ArcGIS REST)",
        category="natural_disasters", connector_type="arcgis_rest",
        source_url="https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query",
    ))
    add_or_update_source(SourceDefinition(
        source_key="portal_sci_data_ics209_demo",
        display_name="ICS-209-PLUS surrogate",
        category="research_reference", connector_type="csv",
        source_url="https://data.oregon.gov/resource/fa7z-shhx.csv",
    ))


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def _haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _extract_points(
    df: pd.DataFrame,
    src_key: str,
    cfg: dict,
    radius_mi: float = QUERY_RADIUS_MI,
) -> pd.DataFrame:
    """Return a DataFrame with clean numeric lat/lon columns, radius-filtered."""
    lat_col = _find_col(df, cfg["lat_candidates"])
    lon_col = _find_col(df, cfg["lon_candidates"])

    if lat_col is None or lon_col is None:
        # EPA fallback: use county centroid
        if src_key == "epa_air_quality" and "county Name" in df.columns:
            rows = []
            seen = set()
            for county in df["county Name"].dropna().unique():
                if county in OREGON_COUNTY_CENTROIDS and county not in seen:
                    lat, lon = OREGON_COUNTY_CENTROIDS[county]
                    rows.append({"lat": lat, "lon": lon, "county": county})
                    seen.add(county)
            return pd.DataFrame(rows)
        return pd.DataFrame(columns=["lat", "lon"])

    pts = df[[lat_col, lon_col]].copy()
    pts.columns = ["lat", "lon"]
    pts["lat"] = pd.to_numeric(pts["lat"], errors="coerce")
    pts["lon"] = pd.to_numeric(pts["lon"], errors="coerce")
    pts = pts.dropna()
    # radius filter
    pts = pts[pts.apply(
        lambda r: _haversine_mi(r["lat"], r["lon"], CENTRE_LAT, CENTRE_LON) <= radius_mi,
        axis=1,
    )]
    return pts.reset_index(drop=True)


def fetch_all() -> dict[str, pd.DataFrame]:
    """Fetch raw DataFrames for every registered source."""
    frames: dict[str, pd.DataFrame] = {}
    for src_key in SOURCE_CONFIG:
        print(f"  Fetching {src_key}…", end=" ", flush=True)
        try:
            defn = get_source(src_key)
            s = make_source(defn)
            df = s.dataframes.get(src_key)
            if df is None or df.empty:
                print("empty")
                continue
            frames[src_key] = df
            print(f"{len(df)} rows")
        except Exception as exc:
            print(f"FAIL — {exc}")
    return frames


# ---------------------------------------------------------------------------
# Spatial geometry
# ---------------------------------------------------------------------------

def build_point_clouds(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Extract radius-filtered lat/lon DataFrames per source."""
    clouds: dict[str, pd.DataFrame] = {}
    for src_key, df in frames.items():
        cfg = SOURCE_CONFIG.get(src_key, {})
        pts = _extract_points(df, src_key, cfg)
        if not pts.empty:
            clouds[src_key] = pts
            print(f"  {src_key}: {len(pts)} points within {QUERY_RADIUS_MI} mi")
        else:
            print(f"  {src_key}: no spatial points")
    return clouds


def build_convex_hulls(clouds: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Return a shapely Polygon (or MultiPoint hull) per source."""
    from shapely.geometry import MultiPoint, Point

    hulls: dict[str, Any] = {}
    for src_key, pts in clouds.items():
        if len(pts) < 3:
            # single point or pair → tiny buffer
            if len(pts) >= 1:
                centroid = Point(pts["lon"].mean(), pts["lat"].mean())
                hulls[src_key] = centroid.buffer(0.1)
            continue
        mp = MultiPoint(list(zip(pts["lon"], pts["lat"])))
        hulls[src_key] = mp.convex_hull
    return hulls


def compute_intersections(hulls: dict[str, Any]) -> list[dict]:
    """Return list of pairwise intersection records."""
    import itertools
    results = []
    keys = list(hulls.keys())
    for a, b in itertools.combinations(keys, 2):
        try:
            inter = hulls[a].intersection(hulls[b])
            if not inter.is_empty:
                area_km2 = inter.area * (111 ** 2)
                results.append({
                    "source_a": a, "source_b": b,
                    "geometry": inter,
                    "area_km2": round(area_km2, 2),
                    "spatial_only": True,
                })
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
# Temporal analysis
# ---------------------------------------------------------------------------

def extract_time_ranges(frames: dict[str, pd.DataFrame]) -> dict[str, tuple]:
    """Return {source_key: (min_date, max_date)} for every source with a date column."""
    ranges: dict[str, tuple] = {}
    for src_key, df in frames.items():
        candidates = DATE_COLS.get(src_key, [])
        for col in candidates:
            if col not in df.columns:
                continue
            parsed = pd.to_datetime(df[col], errors="coerce", utc=False)
            parsed = parsed.dropna()
            if len(parsed) < 2:
                continue
            ranges[src_key] = (parsed.min().to_pydatetime(), parsed.max().to_pydatetime())
            break
    return ranges


def compute_spacetime_intersections(
    hulls: dict[str, Any],
    time_ranges: dict[str, tuple],
) -> list[dict]:
    """Pairwise intersection: spatial hull overlap AND temporal date-range overlap."""
    import itertools
    results = []
    keys = list(hulls.keys())
    for a, b in itertools.combinations(keys, 2):
        # Spatial
        try:
            spatial_inter = hulls[a].intersection(hulls[b])
        except Exception:
            continue
        spatial_ok = not spatial_inter.is_empty

        # Temporal
        ta = time_ranges.get(a)
        tb = time_ranges.get(b)
        if ta and tb:
            t_start = max(ta[0], tb[0])
            t_end   = min(ta[1], tb[1])
            temporal_ok = t_start <= t_end
            overlap_days = max(0, (t_end - t_start).days) if temporal_ok else 0
        else:
            temporal_ok = False
            overlap_days = 0
            t_start = t_end = None

        if spatial_ok or temporal_ok:
            area_km2 = spatial_inter.area * (111 ** 2) if spatial_ok else 0.0
            results.append({
                "source_a": a, "source_b": b,
                "geometry": spatial_inter if spatial_ok else None,
                "area_km2": round(area_km2, 2),
                "spatial_overlap": spatial_ok,
                "temporal_overlap": temporal_ok,
                "overlap_days": overlap_days,
                "time_start": str(t_start.date()) if t_start else None,
                "time_end":   str(t_end.date())   if t_end   else None,
            })
    return results



# ---------------------------------------------------------------------------
# Interactive map (Folium)
# ---------------------------------------------------------------------------

def _poly_to_folium_coords(geom) -> list[list[float]]:
    """Convert shapely polygon exterior to [[lat,lon], ...] for Folium."""
    from shapely.geometry import Polygon, MultiPolygon
    if geom.geom_type == "Polygon":
        return [[y, x] for x, y in geom.exterior.coords]
    elif geom.geom_type == "MultiPolygon":
        coords = []
        for part in geom.geoms:
            coords += [[y, x] for x, y in part.exterior.coords]
        return coords
    return []


def render_folium_map(
    clouds: dict[str, pd.DataFrame],
    hulls: dict[str, Any],
    intersections: list[dict],
    out_path: str,
) -> str:
    import folium
    from folium.plugins import MarkerCluster

    m = folium.Map(
        location=[CENTRE_LAT, CENTRE_LON],
        zoom_start=9,
        tiles=None,
    )

    # --- Tile layers — satellite first so it is the default ---
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite (default)",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Topo",
        name="Topographic",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap",
    ).add_to(m)

    # --- Study-area circle ---
    folium.Circle(
        location=[CENTRE_LAT, CENTRE_LON],
        radius=QUERY_RADIUS_MI * 1609.34,
        color="#333",
        weight=1.5,
        fill=False,
        tooltip=f"Study area: {QUERY_RADIUS_MI} mi radius — Klamath Falls, OR",
    ).add_to(m)
    folium.Marker(
        location=[CENTRE_LAT, CENTRE_LON],
        icon=folium.Icon(color="black", icon="star"),
        tooltip="Klamath Falls, OR (centre)",
    ).add_to(m)

    # --- Intersection polygons — colour by type ---
    inter_group = folium.FeatureGroup(name="Intersections", show=True)
    for rec in intersections:
        geom = rec.get("geometry")
        if geom is None or geom.is_empty:
            continue
        cfg_a = SOURCE_CONFIG.get(rec["source_a"], {})
        cfg_b = SOURCE_CONFIG.get(rec["source_b"], {})
        label_a = cfg_a.get("display", rec["source_a"])
        label_b = cfg_b.get("display", rec["source_b"])
        both = rec.get("spatial_overlap") and rec.get("temporal_overlap")
        fill_color = "#FF4500" if both else "#FFD700"   # red=space+time, gold=space only
        tooltip = (
            f"<b>{'Space ✕ Time' if both else 'Spatial'} Intersection</b><br>"
            f"{label_a} ∩ {label_b}<br>"
            f"Area ≈ {rec['area_km2']} km²"
            + (f"<br>Overlap: {rec['overlap_days']} days ({rec['time_start']} – {rec['time_end']})"
               if rec.get('temporal_overlap') else "")
        )
        try:
            coords = _poly_to_folium_coords(geom)
            if coords:
                folium.Polygon(
                    locations=coords,
                    color=fill_color, weight=2,
                    fill=True, fill_color=fill_color, fill_opacity=0.40,
                    tooltip=tooltip,
                ).add_to(inter_group)
        except Exception:
            pass
    inter_group.add_to(m)

    # --- Convex hull boundaries ---
    hull_group = folium.FeatureGroup(name="Source Footprints", show=True)
    for src_key, hull in hulls.items():
        cfg = SOURCE_CONFIG.get(src_key, {})
        color = cfg.get("color", "#888")
        display = cfg.get("display", src_key)
        try:
            coords = _poly_to_folium_coords(hull)
            if coords:
                folium.Polygon(
                    locations=coords,
                    color=color,
                    weight=2.5,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.10,
                    tooltip=f"<b>{display}</b> spatial footprint",
                ).add_to(hull_group)
        except Exception:
            pass
    hull_group.add_to(m)

    # --- Data points (clustered per source) ---
    for src_key, pts in clouds.items():
        cfg = SOURCE_CONFIG.get(src_key, {})
        color = cfg.get("color", "#888")
        display = cfg.get("display", src_key)
        fg = folium.FeatureGroup(name=f"Points — {display}", show=True)
        cluster = MarkerCluster().add_to(fg)
        sample = pts.sample(min(len(pts), 500), random_state=42)
        for _, row in sample.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f"{display}<br>({row['lat']:.4f}, {row['lon']:.4f})",
            ).add_to(cluster)
        fg.add_to(m)

    # --- Legend ---
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:9999;
                background:rgba(255,255,255,0.92);padding:12px 16px;
                border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.25);
                font-family:sans-serif;font-size:13px;min-width:220px;">
      <b style="font-size:14px">Regional Data Sources</b><br><br>
    """
    for src_key, cfg in SOURCE_CONFIG.items():
        color = cfg.get("color", "#888")
        display = cfg.get("display", src_key)
        legend_html += (
            f'<span style="display:inline-block;width:14px;height:14px;'
            f'background:{color};border-radius:50%;margin-right:6px;'
            f'vertical-align:middle;"></span>{display}<br>'
        )
    legend_html += (
        '<br><span style="display:inline-block;width:14px;height:14px;'
        'background:#FFD700;margin-right:6px;vertical-align:middle;'
        'opacity:0.7;"></span><i>Intersection zone</i>'
        "</div>"
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# Static map (matplotlib + contextily)
# ---------------------------------------------------------------------------

def render_static_map(
    clouds: dict[str, pd.DataFrame],
    hulls: dict[str, Any],
    intersections: list[dict],
    out_path: str,
) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection
    import numpy as np
    from shapely.geometry import Polygon, MultiPolygon, GeometryCollection

    fig, ax = plt.subplots(figsize=(14, 11))

    # Try contextily basemap (needs Web Mercator projection)
    use_ctx = False
    try:
        import contextily as ctx
        all_lats = [CENTRE_LAT]
        all_lons = [CENTRE_LON]
        for pts in clouds.values():
            all_lats += pts["lat"].tolist()
            all_lons += pts["lon"].tolist()
        margin = 0.6
        ax.set_xlim(min(all_lons) - margin, max(all_lons) + margin)
        ax.set_ylim(min(all_lats) - margin, max(all_lats) + margin)
        # Esri WorldImagery = satellite photo background
        ctx.add_basemap(ax, crs="EPSG:4326",
                        source=ctx.providers.Esri.WorldImagery,
                        attribution_size=6, zoom=9)
        use_ctx = True
    except Exception as e:
        print(f"  contextily basemap unavailable ({e}), using plain axes")
        ax.set_facecolor("#1a1a2e")

    # --- Intersection fill ---
    for rec in intersections:
        geom = rec["geometry"]
        polys = []
        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type in ("MultiPolygon", "GeometryCollection"):
            polys = [g for g in geom.geoms if g.geom_type == "Polygon"]
        for poly in polys:
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color="#FFD700", alpha=0.40, zorder=3)
            ax.plot(xs, ys, color="#DAA520", lw=1.2, zorder=4)

    # --- Convex hull outlines ---
    for src_key, hull in hulls.items():
        cfg = SOURCE_CONFIG.get(src_key, {})
        color = cfg.get("color", "#888")
        polys = []
        if hull.geom_type == "Polygon":
            polys = [hull]
        elif hull.geom_type in ("MultiPolygon", "GeometryCollection"):
            polys = [g for g in hull.geoms if g.geom_type == "Polygon"]
        for poly in polys:
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color=color, alpha=0.10, zorder=5)
            ax.plot(xs, ys, color=color, lw=2.0, zorder=6, label=cfg.get("display", src_key))

    # --- Data points ---
    for src_key, pts in clouds.items():
        cfg = SOURCE_CONFIG.get(src_key, {})
        color = cfg.get("color", "#888")
        sample = pts.sample(min(len(pts), 1000), random_state=42)
        ax.scatter(sample["lon"], sample["lat"],
                   c=color, s=12, alpha=0.65, zorder=7, edgecolors="none")

    # --- Centre marker ---
    ax.scatter([CENTRE_LON], [CENTRE_LAT], marker="*", s=280,
               c="#000", zorder=10, label="Klamath Falls, OR")

    # --- Study-area circle (approximate) ---
    theta = [math.radians(i) for i in range(361)]
    # 1 degree lat ≈ 69 mi; 1 degree lon ≈ 69*cos(lat) mi
    r_lat = QUERY_RADIUS_MI / 69.0
    r_lon = QUERY_RADIUS_MI / (69.0 * math.cos(math.radians(CENTRE_LAT)))
    cx = [CENTRE_LON + r_lon * math.cos(t) for t in theta]
    cy = [CENTRE_LAT + r_lat * math.sin(t) for t in theta]
    ax.plot(cx, cy, "--", color="#333", lw=1.2, zorder=8,
            label=f"{QUERY_RADIUS_MI} mi radius")

    ax.set_xlabel("Longitude", fontsize=11)
    ax.set_ylabel("Latitude", fontsize=11)
    ax.set_title(
        f"Regional Data Source Intersection Map\n"
        f"Centre: Klamath Falls, OR  |  {QUERY_RADIUS_MI} mi radius",
        fontsize=13, fontweight="bold",
    )

    # Deduplicate legend
    handles, labels = ax.get_legend_handles_labels()
    seen: dict[str, Any] = {}
    for h, l in zip(handles, labels):
        if l not in seen:
            seen[l] = h
    # Add intersection swatch
    seen["Intersection zone"] = mpatches.Patch(
        facecolor="#FFD700", alpha=0.5, edgecolor="#DAA520")
    ax.legend(seen.values(), seen.keys(),
              loc="lower left", fontsize=9, framealpha=0.85)

    ax.grid(True, linestyle="--", alpha=0.3, zorder=1)
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _render_gantt(time_ranges: dict, intersections: list[dict], out_path: str) -> None:
    """Horizontal Gantt showing temporal coverage per source + overlap bands."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.dates as mdates
    from datetime import datetime

    if not time_ranges:
        return

    keys = list(time_ranges.keys())
    fig, ax = plt.subplots(figsize=(14, max(4, len(keys) * 1.2 + 1.5)))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    colors = {k: SOURCE_CONFIG.get(k, {}).get("color", "#888") for k in keys}

    for i, src_key in enumerate(keys):
        t0, t1 = time_ranges[src_key]
        display = SOURCE_CONFIG.get(src_key, {}).get("display", src_key)
        color = colors[src_key]
        ax.barh(i, (t1 - t0).days, left=mdates.date2num(t0),
                height=0.55, color=color, alpha=0.85, edgecolor="white", linewidth=0.5)
        ax.text(mdates.date2num(t0) + (t1 - t0).days / 2, i,
                f"{t0.strftime('%Y-%m-%d')} → {t1.strftime('%Y-%m-%d')}  ({(t1-t0).days}d)",
                ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")

    # Shade temporal overlap windows
    for rec in intersections:
        if not rec.get("temporal_overlap"):
            continue
        t_start = rec.get("time_start")
        t_end   = rec.get("time_end")
        if not t_start or not t_end:
            continue
        from datetime import date as date_cls
        ts = mdates.date2num(datetime.strptime(t_start, "%Y-%m-%d"))
        te = mdates.date2num(datetime.strptime(t_end,   "%Y-%m-%d"))
        ax.axvspan(ts, te, alpha=0.12, color="#FFD700", zorder=0)

    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels(
        [SOURCE_CONFIG.get(k, {}).get("display", k) for k in keys],
        color="white", fontsize=9,
    )
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=35, ha="right", color="white", fontsize=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.set_title(
        "Temporal Coverage per Data Source\n(gold bands = overlapping periods)",
        color="white", fontsize=12, fontweight="bold",
    )
    ax.set_xlabel("Date", color="white", fontsize=10)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Intersection summary CSV
# ---------------------------------------------------------------------------

def save_intersection_summary(intersections: list[dict], out_path: str) -> str:
    rows = []
    for rec in intersections:
        cfg_a = SOURCE_CONFIG.get(rec["source_a"], {})
        cfg_b = SOURCE_CONFIG.get(rec["source_b"], {})
        rows.append({
            "source_a": cfg_a.get("display", rec["source_a"]),
            "source_b": cfg_b.get("display", rec["source_b"]),
            "intersection_area_km2": rec["area_km2"],
        })
    pd.DataFrame(rows).sort_values("intersection_area_km2", ascending=False).to_csv(
        out_path, index=False
    )
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def project3() -> None:
    print("=" * 60)
    print("Project 3 — Geo-Spatial Intersection Map")
    print(f"Centre: Klamath Falls, OR  ({CENTRE_LAT}, {CENTRE_LON})")
    print(f"Radius: {QUERY_RADIUS_MI} miles")
    print("=" * 60)

    os.makedirs(PLOT_DIR, exist_ok=True)

    # 1. Register & fetch
    print("\n[1/5] Registering sources…")
    register_sources()

    print("\n[2/5] Fetching data…")
    frames = fetch_all()

    # 2. Extract point clouds
    print("\n[3/5] Extracting spatial points…")
    clouds = build_point_clouds(frames)

    if not clouds:
        print("  ✗  No spatial data found — cannot render maps.")
        return

    # 3. Compute hulls + intersections
    print("\n[4/6] Computing convex hulls and space-time intersections…")
    hulls = build_convex_hulls(clouds)
    time_ranges = extract_time_ranges(frames)
    intersections = compute_spacetime_intersections(hulls, time_ranges)
    print(f"  {len(hulls)} source footprints | {len(intersections)} intersecting pairs")
    for rec in intersections:
        a = SOURCE_CONFIG.get(rec["source_a"], {}).get("display", rec["source_a"])
        b = SOURCE_CONFIG.get(rec["source_b"], {}).get("display", rec["source_b"])
        flags = []
        if rec.get("spatial_overlap"): flags.append(f"spatial {rec['area_km2']} km²")
        if rec.get("temporal_overlap"): flags.append(f"temporal {rec['overlap_days']} days")
        print(f"    {a} ∩ {b}  →  {', '.join(flags) or 'no overlap'}")

    print("\n[5/6] Temporal coverage…")
    for src_key, (t0, t1) in time_ranges.items():
        display = SOURCE_CONFIG.get(src_key, {}).get("display", src_key)
        print(f"  {display}: {t0.date()} – {t1.date()} ({(t1-t0).days} days)")

    # 4. Render maps
    print("\n[6/6] Rendering outputs…")

    html_path = os.path.join(PLOT_DIR, "intersection_map.html")
    try:
        render_folium_map(clouds, hulls, intersections, html_path)
        print(f"  ✓  Interactive map → {os.path.abspath(html_path)}")
    except Exception as e:
        print(f"  ✗  Folium map failed: {e}")

    png_path = os.path.join(PLOT_DIR, "intersection_static.png")
    try:
        render_static_map(clouds, hulls, intersections, png_path)
        print(f"  ✓  Static map     → {os.path.abspath(png_path)}")
    except Exception as e:
        print(f"  ✗  Static map failed: {e}")

    # Gantt timeline chart
    gantt_path = os.path.join(PLOT_DIR, "temporal_coverage.png")
    try:
        _render_gantt(time_ranges, intersections, gantt_path)
        print(f"  ✓  Gantt timeline  → {os.path.abspath(gantt_path)}")
    except Exception as e:
        print(f"  ✗  Gantt failed: {e}")

    csv_path = os.path.join(PLOT_DIR, "intersection_summary.csv")
    try:
        save_intersection_summary(intersections, csv_path)
        print(f"  ✓  Summary CSV    → {os.path.abspath(csv_path)}")
    except Exception as e:
        print(f"  ✗  CSV failed: {e}")

    print(f"\n{'=' * 60}")
    print(f"Done — outputs in {os.path.abspath(PLOT_DIR)}/")


if __name__ == "__main__":
    project3()

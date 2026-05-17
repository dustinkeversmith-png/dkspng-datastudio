from app.workflow.source_binding import Source

def intersection_buffer(source: Source, base_key: str, sec_key: str, buffer_deg: float = 0.01) -> dict:
    """Find intersections natively using geopandas."""
    if base_key not in source.dataframes or sec_key not in source.dataframes:
        return {"error": "Missing sources"}
        
    base_df = source.dataframes[base_key]
    sec_df = source.dataframes[sec_key]
    
    try:
        import geopandas as gpd
        b_x = "longitude" if "longitude" in base_df.columns else "lon"
        b_y = "latitude" if "latitude" in base_df.columns else "lat"
        s_x = "longitude" if "longitude" in sec_df.columns else "lon"
        s_y = "latitude" if "latitude" in sec_df.columns else "lat"
        
        if b_x not in base_df.columns or s_x not in sec_df.columns:
            return {"error": "Missing coordinate columns for GIS intersection."}
            
        base_gdf = gpd.GeoDataFrame(base_df, geometry=gpd.points_from_xy(base_df[b_x], base_df[b_y]), crs="EPSG:4326")
        sec_gdf = gpd.GeoDataFrame(sec_df, geometry=gpd.points_from_xy(sec_df[s_x], sec_df[s_y]), crs="EPSG:4326")
        
        base_gdf["geometry"] = base_gdf.geometry.buffer(buffer_deg)
        intersect = gpd.sjoin(base_gdf, sec_gdf, how="inner", predicate="intersects")
        
        return {
            "status": "success",
            "intersections_found": len(intersect)
        }
    except ImportError:
        return {"error": "geopandas missing, returning topological metadata stub", "status": "fallback"}

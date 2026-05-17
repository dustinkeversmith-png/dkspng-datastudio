from typing import Any, Dict, List
import pandas as pd
from app.analyzers.base_analyzer import BaseAnalyzer
from app.core.context import ExecutionContext
from app.core.validation import ValidationResult
from app.core.result import ComponentResult
from app.core.lineage import create_lineage_record
from app.mappings.mapping_targets import ResolvedMapping

class SpatialIntegrator(BaseAnalyzer):
    def __init__(self, target_mapping: ResolvedMapping, secondary_source_keys: List[str], buffer_deg: float = 0.01):
        self.target_mapping = target_mapping
        self.secondary_source_keys = secondary_source_keys
        self.buffer_deg = buffer_deg

    @property
    def component_key(self) -> str:
        return "spatial_integrator"

    @property
    def display_name(self) -> str:
        return "Spatial Integrator"

    def validate(self, context: ExecutionContext) -> ValidationResult:
        spatial_x = self.target_mapping.by_role("spatial_x")
        spatial_y = self.target_mapping.by_role("spatial_y")
        spatial_geom = self.target_mapping.by_role("spatial_geometry")
        
        if not (spatial_geom or (spatial_x and spatial_y)):
            return ValidationResult.failure(["Target mapping must contain 'spatial_geometry' or both 'spatial_x' and 'spatial_y' roles."])
            
        return ValidationResult.success()

    def execute(self, context: ExecutionContext) -> ComponentResult:
        from app.core.selectors import select_source_dataframe
        
        base_df = select_source_dataframe(context.source, context.source_key)
        
        # Determine coordinate fields for base source
        x_col = self.target_mapping.by_role("spatial_x")[0].selector.get("name") if self.target_mapping.by_role("spatial_x") else "longitude"
        y_col = self.target_mapping.by_role("spatial_y")[0].selector.get("name") if self.target_mapping.by_role("spatial_y") else "latitude"

        # Attempt to use geopandas if available, else fallback to naive cartesian join approximation
        try:
            import geopandas as gpd
            from shapely.geometry import Point
            
            # Base geometry
            base_gdf = gpd.GeoDataFrame(
                base_df, 
                geometry=gpd.points_from_xy(base_df[x_col], base_df[y_col]),
                crs="EPSG:4326"
            )
            base_gdf["geometry"] = base_gdf.geometry.buffer(self.buffer_deg)
            
            integrated_df = base_gdf

            for sec_key in self.secondary_source_keys:
                sec_df = select_source_dataframe(context.source, sec_key)
                
                # We assume secondary sources share similar col names for this phase testing, 
                # or we'd ideally pass mappings for each source.
                sec_x = x_col if x_col in sec_df.columns else "lon"
                sec_y = y_col if y_col in sec_df.columns else "lat"
                
                if sec_x in sec_df.columns and sec_y in sec_df.columns:
                    sec_gdf = gpd.GeoDataFrame(
                        sec_df, 
                        geometry=gpd.points_from_xy(sec_df[sec_x], sec_df[sec_y]),
                        crs="EPSG:4326"
                    )
                    
                    integrated_df = gpd.sjoin(integrated_df, sec_gdf, how="left", predicate="intersects")
            
            final_df = pd.DataFrame(integrated_df.drop(columns=["geometry", "index_right"], errors="ignore"))

        except ImportError:
            # Fallback naive pandas merge (exact coordinate match or approximate rounding)
            base_df["_join_x"] = base_df[x_col].round(2)
            base_df["_join_y"] = base_df[y_col].round(2)
            final_df = base_df
            
            for sec_key in self.secondary_source_keys:
                sec_df = select_source_dataframe(context.source, sec_key)
                sec_x = x_col if x_col in sec_df.columns else "lon"
                sec_y = y_col if y_col in sec_df.columns else "lat"
                
                if sec_x in sec_df.columns and sec_y in sec_df.columns:
                    sec_df["_join_x"] = sec_df[sec_x].round(2)
                    sec_df["_join_y"] = sec_df[sec_y].round(2)
                    final_df = final_df.merge(sec_df, on=["_join_x", "_join_y"], how="left", suffixes=("", f"_{sec_key}"))

            final_df = final_df.drop(columns=["_join_x", "_join_y"])

        lineage = create_lineage_record(context.source_key or "unknown", self.component_key, {"secondary_sources": self.secondary_source_keys})
        return ComponentResult(
            component_key=self.component_key,
            result_type="composite_dataframe",
            data=final_df,
            lineage=lineage
        )

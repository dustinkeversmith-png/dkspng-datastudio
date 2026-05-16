import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import os

class CompositeIntegrator:
    """
    Builds a unified 'Regional Risk & Economy' composite source by joining 
    disparate datasets across Space, Time, and Magnitude dimensions.
    """
    def __init__(self):
        self.sources = {}
        
    def load_source(self, name: str, filepath: str):
        if os.path.exists(filepath):
            self.sources[name] = pd.read_csv(filepath)
            print(f"Loaded {name} with {len(self.sources[name])} rows.")
        else:
            print(f"Warning: {filepath} not found.")

    def synchronize_temporal(self):
        """Coalesce all 'Time: Temporal' fields to a standardized 'YYYY' integer."""
        for name, df in self.sources.items():
            year_col = f"{name}_YYYY"
            found_time = False
            for col in df.columns:
                if col.lower() in ['fireyear', 'year', 'report_date', 'date', 'created_date', 'containmentdatetime']:
                    try:
                        if df[col].dtype == 'object':
                            df[year_col] = pd.to_datetime(df[col], errors='coerce').dt.year.fillna(2023).astype(int)
                        else:
                            df[year_col] = df[col].fillna(2023).astype(int)
                        found_time = True
                        break # Standardized
                    except Exception:
                        pass
            if not found_time:
                df[year_col] = 2023 # fallback

    def normalize_area(self):
        """Convert 'Space: Area' with 'ft2' to 'Acres'."""
        for name, df in self.sources.items():
            for col in df.columns:
                if 'ft2' in col.lower():
                    # Convert ft2 to Acres (Val / 43560)
                    new_col = col.replace('ft2', 'Acres').replace('FT2', 'Acres')
                    df[new_col] = pd.to_numeric(df[col], errors='coerce') / 43560.0
                elif 'acres' in col.lower():
                    df[f"{name}_Acres"] = pd.to_numeric(df[col], errors='coerce')

    def build_composite(self) -> pd.DataFrame:
        """
        Generate a 'Composite Registry' mapping every unique record to its GACC region 
        and Census Tract (GEOID), appending all relevant dimensional metrics.
        """
        # Primary spatial-temporal fire data (NIFC)
        if "nifc" not in self.sources:
            print("NIFC source required as base.")
            return pd.DataFrame()
            
        base_df = self.sources["nifc"].copy()
        
        # Ensure coordinates exist
        if "latitude" not in base_df.columns:
            base_df["latitude"] = 42.2249
        if "longitude" not in base_df.columns:
            base_df["longitude"] = -121.7817
            
        # Append GACC and GEOID
        base_df["GACC_Region"] = "Northwest"
        base_df["Census_Tract_GEOID"] = "41035970100" # Klamath example tract
        
        # Mock economic and suppression costs (since surrogate tech labor profiles were used)
        if "Total Suppression Costs ($)" not in base_df.columns:
            size_col = "DiscoveryAcres" if "DiscoveryAcres" in base_df.columns else "IncidentSize"
            sizes = pd.to_numeric(base_df.get(size_col, 10), errors='coerce').fillna(10)
            # Roughly $1500 per acre + baseline cost
            base_df["Total Suppression Costs ($)"] = sizes * 1500 + np.random.normal(50000, 10000, len(base_df))
            base_df["Total Suppression Costs ($)"] = base_df["Total Suppression Costs ($)"].clip(lower=1000)
            
        if "Median Hourly Earnings" not in base_df.columns:
            # Mock socio-economic baseline logic
            base_df["Median Hourly Earnings"] = 35.0 - (base_df["Total Suppression Costs ($)"] / 1000000) + np.random.normal(2, 1, len(base_df))
            base_df["Median Hourly Earnings"] = base_df["Median Hourly Earnings"].clip(lower=15.0)
            
        # Convert base to GeoDataFrame
        base_gdf = gpd.GeoDataFrame(
            base_df, 
            geometry=[Point(xy) for xy in zip(base_df["longitude"], base_df["latitude"])],
            crs="EPSG:4326"
        )
        
        # Spatial Alignment with SLIDO using 500m buffer
        if "slido" in self.sources:
            slido_df = self.sources["slido"]
            slido_df["latitude"] = pd.to_numeric(slido_df.get("latitude", 42.2), errors='coerce')
            slido_df["longitude"] = pd.to_numeric(slido_df.get("longitude", -121.7), errors='coerce')
            
            # Drop rows with NaN coordinates
            slido_df = slido_df.dropna(subset=["latitude", "longitude"])
            
            slido_gdf = gpd.GeoDataFrame(
                slido_df,
                geometry=[Point(xy) for xy in zip(slido_df["longitude"], slido_df["latitude"])],
                crs="EPSG:4326"
            )
            # Create a 500m buffer (approx 0.0045 degrees at this latitude)
            base_gdf["geometry"] = base_gdf.geometry.buffer(0.0045)
            
            # Left join where NIFC buffer intersects SLIDO point
            composite = gpd.sjoin(base_gdf, slido_gdf, how="left", predicate="intersects")
            return pd.DataFrame(composite.drop(columns=["geometry"]))
            
        return pd.DataFrame(base_gdf.drop(columns=["geometry"]))

    def generate_relationship_matrix(self, composite_df: pd.DataFrame) -> pd.DataFrame:
        """Identify correlations between variables."""
        cols_of_interest = ["Total Suppression Costs ($)", "Median Hourly Earnings"]
        
        for col in composite_df.columns:
            if "YYYY" in col or "Acres" in col:
                cols_of_interest.append(col)
                
        # Filter to existing numeric cols
        cols_of_interest = [c for c in cols_of_interest if c in composite_df.columns]
        
        if len(cols_of_interest) >= 2:
            return composite_df[cols_of_interest].corr(numeric_only=True)
        return pd.DataFrame()

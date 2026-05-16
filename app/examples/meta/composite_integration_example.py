import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.composite_source_analysis import CompositeIntegrator

def run_composite_integration_example():
    integrator = CompositeIntegrator()
    
    print("--- Loading Sources ---")
    # 1. Primary spatial-temporal fire data
    integrator.load_source("nifc", "data/nifc_northwest_incidents.csv")
    
    # 2. Comparative ignition and land-ownership metrics
    integrator.load_source("odf", "data/klamath_falls_odf_firestats.csv")
    
    # 3. Secondary geologic hazard overlays
    integrator.load_source("slido", "data/klamath_falls_slido.csv")
    
    # 4. Socio-economic baseline data (using EMSI postings surrogate)
    integrator.load_source("labor", "data/p19_table_01_emsi_postings.csv")

    print("\n--- Applying Dimensional Matching & Conversions ---")
    integrator.synchronize_temporal()
    integrator.normalize_area()
    
    print("\n--- Building Composite Source ---")
    composite_df = integrator.build_composite()
    
    if composite_df.empty:
        print("Failed to build composite dataframe.")
        return

    print(f"\nComposite Registry created with {len(composite_df)} rows and {len(composite_df.columns)} columns.")
    
    # Preview Dataset Overview
    print("\n[Dataset Overview Preview]")
    preview_cols = ["GACC_Region", "Census_Tract_GEOID", "Total Suppression Costs ($)", "Median Hourly Earnings"]
    # Add any YYYY or Acres cols
    for col in composite_df.columns:
        if "YYYY" in col or "Acres" in col:
            preview_cols.append(col)
            
    # Deduplicate keeping order
    preview_cols = list(dict.fromkeys([c for c in preview_cols if c in composite_df.columns]))
    print(composite_df[preview_cols].head())
    
    # Output schema artifact
    os.makedirs("artifacts", exist_ok=True)
    overview_path = "artifacts/composite_dataset_overview.csv"
    composite_df.to_csv(overview_path, index=False)
    print(f"\nDataset Overview artifact saved to: {overview_path}")

    print("\n--- Generating Relationship Interest ---")
    corr_matrix = integrator.generate_relationship_matrix(composite_df)
    
    print("\n[Relationship Matrix Preview]")
    print(corr_matrix)
    
    # Output matrix artifact
    matrix_path = "artifacts/composite_relationship_matrix.csv"
    corr_matrix.to_csv(matrix_path)
    print(f"\nRelationship Matrix artifact saved to: {matrix_path}")

if __name__ == "__main__":
    run_composite_integration_example()

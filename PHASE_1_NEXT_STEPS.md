# Phase 1 next steps

1. Replace placeholder ArcGIS URLs in `app/source_registry.py`.
2. Add source-specific field maps:
   - ODF Fire Occurrence GIS
   - DOGAMI SLIDO landslides
   - OHA traffic/micromobility injuries
   - workforce report table extraction
3. Add raw file archiving.
4. Add duplicate detection.
5. Add dataset versioning.
6. Add query route:
   - `/observations/query?bbox=&county=&year_min=&year_max=&category=`
7. Add export routes:
   - `/exports/geojson`
   - `/exports/parquet`
   - `/exports/csv`

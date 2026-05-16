# Data Identity Card: hazard_spatial_boundaries

## Source Lineage
- **URL**: local://hazard_spatial_boundaries.csv
- **Fetched At**: 2026-05-16T02:57:13.491116
- **Patch Row Count**: 18

## Column Index
| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |
|-------------|---------------|----------|-------|--------|-------------|
| REF_ID_COD | string | unique_identifier | 0 | 1 | - |
| UNIQUE_ID | string | unique_identifier | 0 | 18 | - |
| DATA_SOURC | categorical | label_lookup | 0 | 1 | - |
| LOC_METHOD | categorical | label_lookup | 0 | 1 | - |
| ORIG_ID | string | unique_identifier | 0 | 18 | - |
| SLIDE_NAME | categorical | label_lookup | 0 | 1 | - |
| LENGTH_ft | numeric | ft | 0 | 1 | - |
| WIDTH_ft | numeric | ft | 0 | 1 | - |
| DEPTH_ft | numeric | ft | 0 | 1 | - |
| SLOPE | numeric | slope | 0 | 1 | - |
| TYPE_MOVE | categorical | label_lookup | 0 | 1 | - |
| MOVE_CLASS | categorical | label_lookup | 0 | 1 | - |
| CONTR_FACT | categorical | label_lookup | 0 | 1 | - |
| TYPE_MTRL | categorical | label_lookup | 0 | 1 | - |
| AREA_ft2 | numeric | ft2 | 0 | 1 | - |
| VOLUME_ft3 | numeric | ft3 | 0 | 1 | - |
| DEEP_SHAL | categorical | label_lookup | 0 | 1 | - |
| DAMAGES | string | - | 0 | 7 | - |
| LOSSES | categorical | label_lookup | 0 | 1 | - |
| COMMENTS | string | - | 0 | 18 | - |
| YEAR | datetime | temporal | 0 | 1 | - |
| DATE_RANGE | datetime | temporal | 0 | 1 | - |
| MONTH | datetime | temporal | 0 | 1 | - |
| DAY | datetime | temporal | 0 | 1 | - |
| FID | numeric | unique_identifier | 0 | 18 | - |
| ANNUAL_COS | numeric | - | 0 | 12 | - |
| REPAIR_COS | numeric | - | 0 | 14 | - |
| REACTIVATI | categorical | label_lookup | 0 | 1 | - |
| longitude | float | decimal_degrees | 0 | 18 | - |
| latitude | float | decimal_degrees | 0 | 18 | - |
| session_source_key | categorical | label_lookup | 0 | 1 | - |

## Data Sample (Top 5 Rows)
| REF_ID_COD | UNIQUE_ID | DATA_SOURC | LOC_METHOD | ORIG_ID | SLIDE_NAME | LENGTH_ft | WIDTH_ft | DEPTH_ft | SLOPE | TYPE_MOVE | MOVE_CLASS | CONTR_FACT | TYPE_MTRL | AREA_ft2 | VOLUME_ft3 | DEEP_SHAL | DAMAGES | LOSSES | COMMENTS | YEAR | DATE_RANGE | MONTH | DAY | FID | ANNUAL_COS | REPAIR_COS | REACTIVATI | longitude | latitude | session_source_key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ODOT2011 | LS_70 | Oregon Department of Transportation |   | SL004-0241-43RS1 |   | 0 | 0 | 0 | 0 |   | Rockfall |   |   | 0 | 0 |   | Road Impact:RF on roadway;Lanes Affected:1; |   |  Hwy Name:The Dalles-California; Hwy Number:004;Mile Post:241.63;Frequency:every yr;mitigated, no new history needed | 0 |   |   |   | 70 | 0.0 | 0.0 |   | -121.85857886644963 | 42.67201170553657 | census_tiger_boundaries |
| ODOT2011 | LS_71 | Oregon Department of Transportation |   | SL004-0241-62RS1 |   | 0 | 0 | 0 | 0 |   | Rockfall |   |   | 0 | 0 |   | Road Impact:RF on roadway;Lanes Affected:1; |   |  Hwy Name:The Dalles-California; Hwy Number:004;Mile Post:241.62;Frequency:every yr;mitigated, no new history needed | 0 |   |   |   | 71 | 0.0 | 0.0 |   | -121.85937540563964 | 42.66927808001442 | census_tiger_boundaries |
| ODOT2011 | LS_72 | Oregon Department of Transportation |   | SL004-0241-80RS1 |   | 0 | 0 | 0 | 0 |   | Rockfall |   |   | 0 | 0 |   | Road Impact:RF on roadway;Lanes Affected:1; |   |  Hwy Name:The Dalles-California; Hwy Number:004;Mile Post:241.8;Frequency:every yr;mitigated, no new history needed | 0 |   |   |   | 72 | 0.0 | 0.0 |   | -121.86116029376414 | 42.66708187671151 | census_tiger_boundaries |
| ODOT2011 | LS_73 | Oregon Department of Transportation |   | SL004-0241-98RS1 |   | 0 | 0 | 0 | 0 |   | Rockfall |   |   | 0 | 0 |   | Road Impact:RF on roadway;Lanes Affected:2; |   |  Hwy Name:The Dalles-California; Hwy Number:004;Mile Post:241.98;Frequency:every yr;mitigated, no new history needed | 0 |   |   |   | 73 | 0.0 | 0.0 |   | -121.86403473989218 | 42.66577623103929 | census_tiger_boundaries |
| ODOT2011 | LS_74 | Oregon Department of Transportation |   | SL004-0242-34RS1 |   | 0 | 0 | 0 | 0 |   | Rockfall |   |   | 0 | 0 |   | Road Impact:RF on roadway;Lanes Affected:2; |   |  Hwy Name:The Dalles-California; Hwy Number:004;Mile Post:242.34;Frequency:every yr;mitigated, no new history needed | 0 |   |   |   | 74 | 0.0 | 0.0 |   | -121.8709442612602 | 42.66511474569281 | census_tiger_boundaries |

# Data Identity Card: portal_dogami_slido

## Source Lineage
- **URL**: https://gis.dogami.oregon.gov/arcgis/rest/services/Public/SLIDO42/MapServer/0/query
- **Fetched At**: 2026-05-16T01:06:40.055065
- **Patch Row Count**: 52

## Column Index
| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |
|-------------|---------------|----------|-------|--------|-------------|
| REF_ID_COD | string | unique_identifier | 0 | 2 | - |
| UNIQUE_ID | string | unique_identifier | 0 | 52 | - |
| DATA_SOURC | categorical | label_lookup | 0 | 4 | - |
| LOC_METHOD | categorical | label_lookup | 0 | 4 | - |
| ORIG_ID | string | unique_identifier | 0 | 52 | - |
| SLIDE_NAME | string | - | 0 | 17 | - |
| LENGTH_ft | numeric | ft | 0 | 3 | - |
| WIDTH_ft | numeric | ft | 0 | 3 | - |
| DEPTH_ft | numeric | ft | 0 | 1 | - |
| SLOPE | numeric | slope | 0 | 1 | - |
| TYPE_MOVE | categorical | label_lookup | 0 | 1 | - |
| MOVE_CLASS | string | - | 0 | 6 | - |
| CONTR_FACT | categorical | label_lookup | 0 | 2 | - |
| TYPE_MTRL | categorical | label_lookup | 0 | 3 | - |
| AREA_ft2 | numeric | ft2 | 0 | 1 | - |
| VOLUME_ft3 | numeric | ft3 | 0 | 3 | - |
| DEEP_SHAL | categorical | label_lookup | 0 | 1 | - |
| DAMAGES | string | - | 0 | 27 | - |
| LOSSES | categorical | label_lookup | 0 | 1 | - |
| COMMENTS | string | - | 0 | 49 | - |
| YEAR | datetime | temporal | 0 | 1 | - |
| DATE_RANGE | datetime | temporal | 0 | 2 | - |
| MONTH | datetime | temporal | 0 | 1 | - |
| DAY | datetime | temporal | 0 | 1 | - |
| FID | numeric | unique_identifier | 0 | 52 | - |
| ANNUAL_COS | numeric | - | 0 | 6 | - |
| REPAIR_COS | numeric | - | 0 | 33 | - |
| REACTIVATI | categorical | label_lookup | 0 | 1 | - |
| longitude | float | decimal_degrees | 0 | 52 | - |
| latitude | float | decimal_degrees | 0 | 52 | - |
| session_source_key | categorical | label_lookup | 0 | 1 | - |

## Data Sample (Top 5 Rows)
| REF_ID_COD | UNIQUE_ID | DATA_SOURC | LOC_METHOD | ORIG_ID | SLIDE_NAME | LENGTH_ft | WIDTH_ft | DEPTH_ft | SLOPE | TYPE_MOVE | MOVE_CLASS | CONTR_FACT | TYPE_MTRL | AREA_ft2 | VOLUME_ft3 | DEEP_SHAL | DAMAGES | LOSSES | COMMENTS | YEAR | DATE_RANGE | MONTH | DAY | FID | ANNUAL_COS | REPAIR_COS | REACTIVATI | longitude | latitude | session_source_key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ODOT2011 | LS_1682 | Oregon Department of Transportation |   | SL021-0011-84BB1 |   | 0 | 0 | 0.0 | 0 |   | Fill Failure |   |   | 0 | 0 |   | Road Impact:LS close 10-60mi det;Lanes Affected:2; |   |  Hwy Name:Green Springs; Hwy Number:021;Mile Post:11.84;Frequency:every 3 yrs; | 0 |   |   |   | 1656 | 0.0 | 0.0 |   | -122.53487675358278 | 42.13014857366428 | portal_dogami_slido |
| ODOT2011 | LS_2436 | Oregon Department of Transportation |   | SL270-0018-73RE1 | Slide 1 | 0 | 0 | 0.0 | 0 |   | Fill Failure |   |   | 0 | 0 |   | Road Impact:LS leaves 2-way traf;Lanes Affected:1; |   |  Hwy Name:Lake of the Woods; Hwy Number:270;Mile Post:18.73;Frequency:every yr; | 0 |   |   |   | 2037 | 600.0 | 389567.0 |   | -122.53510109549399 | 42.40268820143402 | portal_dogami_slido |
| ODOT2011 | LS_2437 | Oregon Department of Transportation |   | SL270-0018-84RE1 | N/A | 0 | 0 | 0.0 | 0 |   | Fill Failure |   |   | 0 | 0 |   | Road Impact:LS leaves 2-way traf;Lanes Affected:1; |   |  Hwy Name:Lake of the Woods; Hwy Number:270;Mile Post:18.84;Frequency:every 5 yrs or less; | 0 |   |   |   | 2038 | 0.0 | 95000.0 |   | -122.53300264282122 | 42.4020995606169 | portal_dogami_slido |
| ODOT2011 | LS_2438 | Oregon Department of Transportation |   | SL270-0019-16RE1 | N/A | 0 | 0 | 0.0 | 0 |   | Fill Failure |   |   | 0 | 0 |   | Road Impact:LS affects shoulder; |   |  Hwy Name:Lake of the Woods; Hwy Number:270;Mile Post:19.16;Frequency:every 2 yrs; | 0 |   |   |   | 2039 | 300.0 | 329300.0 |   | -122.52720826395698 | 42.401030083994996 | portal_dogami_slido |
| ODOT2011 | LS_2439 | Oregon Department of Transportation |   | SL270-0019-40RE1 | Slide 2 | 0 | 0 | 0.0 | 0 |   | Fill Failure |   |   | 0 | 0 |   | Road Impact:LS affects shoulder; |   |  Hwy Name:Lake of the Woods; Hwy Number:270;Mile Post:19.4;Frequency:every 5 yrs or less; | 0 |   |   |   | 2040 | 0.0 | 8606.0 |   | -122.52262859913563 | 42.400258245941565 | portal_dogami_slido |

# Data Identity Card: p22_table_01_h1b_visas

## Source Lineage
- **URL**: local://p22_table_01_h1b_visas.csv
- **Fetched At**: 2026-05-16T02:57:13.596108
- **Patch Row Count**: 4

## Column Index
| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |
|-------------|---------------|----------|-------|--------|-------------|
| serial | numeric | - | 0 | 4 | - |
| firecategory | string | - | 0 | 1 | - |
| fireyear | numeric | - | 0 | 2 | - |
| area | numeric | area | 0 | 1 | - |
| districtname | string | - | 0 | 1 | - |
| unitname | string | - | 0 | 1 | - |
| fullfirenumber | string | - | 0 | 4 | - |
| complexname | string | - | 0 | 4 | - |
| firename | string | - | 0 | 4 | - |
| size_class | string | - | 0 | 1 | - |
| esttotalacres | numeric | - | 0 | 2 | - |
| protected_acres | numeric | - | 0 | 2 | - |
| humanorlightning | string | - | 0 | 2 | - |
| causeby | string | - | 0 | 2 | - |
| generalcause | string | - | 0 | 2 | - |
| specificcause | string | - | 0 | 2 | - |
| cause_comments | string | - | 0 | 2 | - |
| lat_dd | float | decimal_degrees | 0 | 4 | - |
| long_dd | float | decimal_degrees | 0 | 4 | - |
| latlongddpoint | string | - | 0 | 4 | - |
| fo_landowntype | string | - | 0 | 3 | - |
| twn | string | - | 0 | 3 | - |
| rng | string | - | 0 | 2 | - |
| sec | numeric | - | 0 | 4 | - |
| subdiv | string | - | 0 | 4 | - |
| landmarklocation | string | - | 0 | 4 | - |
| county | string | - | 0 | 1 | - |
| regusezone | string | - | 0 | 2 | - |
| reguserestriction | string | - | 0 | 2 | - |
| industrial_restriction | string | - | 0 | 3 | - |
| ign_datetime | string | - | 0 | 4 | - |
| reportdatetime | string | - | 0 | 4 | - |
| discover_datetime | string | - | 0 | 4 | - |
| control_datetime | string | - | 0 | 4 | - |
| creationdate | string | - | 0 | 4 | - |
| modifieddate | string | - | 0 | 4 | - |
| districtcode | numeric | - | 0 | 1 | - |
| unitcode | numeric | - | 0 | 1 | - |
| distfirenumber | numeric | - | 0 | 4 | - |
| session_source_key | string | - | 0 | 1 | - |

## Data Sample (Top 5 Rows)
| serial | firecategory | fireyear | area | districtname | unitname | fullfirenumber | complexname | firename | size_class | esttotalacres | protected_acres | humanorlightning | causeby | generalcause | specificcause | cause_comments | lat_dd | long_dd | latlongddpoint | fo_landowntype | twn | rng | sec | subdiv | landmarklocation | county | regusezone | reguserestriction | industrial_restriction | ign_datetime | reportdatetime | discover_datetime | control_datetime | creationdate | modifieddate | districtcode | unitcode | distfirenumber | session_source_key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 77291 | STAT | 2007 | SOA | Southwest Oregon | Medford | 07-711168-07 | 6/2 Complex | 6/2 Complex  Millmar | A | 0.01 | 0.01 | Lightning | Lightning | Lightning | Lightning | nan | 42.68361 | -122.42444 | POINT (-122.42444 42.68361) | Industrial | 33S | 03E | 23 | NESE | 12 miles NE of Butte Falls | Jackson | SW2 | Outside Closed Fire Season | Outside Closed Fire Season | 2007 Jun 02 01:00:00 AM | 2007 Jun 02 10:00:00 AM | 2007 Jun 02 09:50:00 AM | 2007 Jun 02 01:00:00 PM | 2007 Jun 04 10:21:00 AM | 2007 Oct 15 01:14:00 PM | 71 | 711 | 168 | dol_h1b_records |
| 77887 | STAT | 2007 | SOA | Southwest Oregon | Medford | 07-711030-08 | 7/10 Complex | 7/10 Complex Hyatt Lake | A | 0.01 | 0.01 | Lightning | Lightning | Lightning | Lightning | nan | 42.18639 | -122.45667 | POINT (-122.45667 42.18639) | BLM | 39S | 03E | 10 | SESW | 13 Mi E of Ashland | Jackson | SW2 | Reg Use Closure | Lvl 1 Fire Season Only | 2007 Jul 10 10:00:00 PM | 2007 Jul 10 10:19:00 PM | 2007 Jul 10 10:15:00 PM | 2007 Jul 10 11:00:00 PM | 2007 Jul 13 12:00:00 AM | 2007 Jul 21 01:04:00 PM | 71 | 711 | 30 | dol_h1b_records |
| 81830 | STAT | 2008 | SOA | Southwest Oregon | Medford | 08-711058-09 | 8/16 Complex | 8/16 Complex | A | 0.1 | 0.0 | Lightning | Lightning | Lightning | Lightning | nan | 42.68694 | -122.39528 | POINT (-122.39528 42.68694) | USFS | 33S | 04E | 19 | SENW | 13 Miles NE of Butte Falls | Jackson | RR1 | Reg Use Closure | Lvl 2 Limited Shutdown | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 07:39:00 PM | 2008 Aug 16 12:00:00 AM | 2008 Dec 16 02:37:00 PM | 71 | 711 | 58 | dol_h1b_records |
| 82745 | STAT | 2008 | SOA | Southwest Oregon | Medford | 08-711106-09 | 9/16 Complex | 9/16 Complex | A | 0.01 | 0.01 | Human | Timber Harvest Worker | Equipment Use | Other -Equipment Use Related (ie. road const., other i.c.e.) | Hot Saw | 42.61139 | -122.49778 | POINT (-122.49778 42.61139) | Industrial | 34S | 03E | 17 | NWSW | 10 Mi SE of Butte Falls | Jackson | SW2 | Reg Use Closure | Lvl 2 Limited Shutdown | 2008 Sep 16 04:00:00 PM | 2008 Sep 16 08:03:00 PM | 2008 Sep 16 08:03:00 PM | 2008 Sep 16 10:18:00 PM | 2008 Sep 17 12:00:00 AM | 2008 Sep 24 09:25:00 AM | 71 | 711 | 106 | dol_h1b_records |

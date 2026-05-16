# Data Identity Card: portal_sci_data_ics209_demo

## Source Lineage
- **URL**: https://doi.org/10.1038/s41597-023-01955-0
- **Documentation**: https://api.datacite.org/works/10.1038/s41597-023-01955-0
- **Fetched At**: 2026-05-16T02:26:33.202048
- **Patch Row Count**: 100

## Column Index
| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |
|-------------|---------------|----------|-------|--------|-------------|
| serial | numeric | - | 0 | 100 | - |
| firecategory | categorical | label_lookup | 0 | 1 | - |
| fireyear | numeric | - | 0 | 22 | - |
| area | numeric | area | 0 | 2 | - |
| districtname | categorical | label_lookup | 0 | 3 | - |
| unitname | categorical | label_lookup | 0 | 3 | - |
| fullfirenumber | string | - | 0 | 100 | - |
| complexname | string | - | 0 | 12 | - |
| firename | string | - | 0 | 99 | - |
| size_class | categorical | label_lookup | 0 | 7 | - |
| esttotalacres | numeric | - | 0 | 82 | - |
| protected_acres | numeric | - | 0 | 83 | - |
| humanorlightning | categorical | label_lookup | 0 | 3 | - |
| causeby | string | - | 0 | 12 | - |
| generalcause | categorical | label_lookup | 0 | 8 | - |
| specificcause | string | - | 0 | 28 | - |
| cause_comments | string | - | 0 | 42 | - |
| lat_dd | float | decimal_degrees | 0 | 99 | - |
| long_dd | float | decimal_degrees | 0 | 99 | - |
| latlongddpoint | string | - | 0 | 99 | - |
| fo_landowntype | categorical | label_lookup | 0 | 9 | - |
| twn | string | - | 0 | 13 | - |
| rng | string | - | 0 | 25 | - |
| sec | numeric | - | 0 | 34 | - |
| subdiv | string | - | 0 | 17 | - |
| landmarklocation | string | - | 0 | 97 | - |
| county | categorical | label_lookup | 0 | 5 | - |
| regusezone | categorical | label_lookup | 0 | 7 | - |
| reguserestriction | categorical | label_lookup | 0 | 7 | - |
| industrial_restriction | categorical | label_lookup | 0 | 8 | - |
| ign_datetime | string | - | 0 | 85 | - |
| reportdatetime | string | - | 0 | 99 | - |
| discover_datetime | string | - | 0 | 94 | - |
| control_datetime | string | - | 0 | 94 | - |
| creationdate | string | - | 0 | 90 | - |
| modifieddate | string | - | 0 | 100 | - |
| districtcode | categorical | label_lookup | 0 | 2 | - |
| unitcode | categorical | label_lookup | 0 | 3 | - |
| distfirenumber | numeric | - | 0 | 85 | - |
| session_source_key | categorical | label_lookup | 0 | 1 | - |

## Data Sample (Top 5 Rows)
| serial | firecategory | fireyear | area | districtname | unitname | fullfirenumber | complexname | firename | size_class | esttotalacres | protected_acres | humanorlightning | causeby | generalcause | specificcause | cause_comments | lat_dd | long_dd | latlongddpoint | fo_landowntype | twn | rng | sec | subdiv | landmarklocation | county | regusezone | reguserestriction | industrial_restriction | ign_datetime | reportdatetime | discover_datetime | control_datetime | creationdate | modifieddate | districtcode | unitcode | distfirenumber | session_source_key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 77291 | STAT | 2007 | SOA | Southwest Oregon | Medford | 07-711168-07 | 6/2 Complex | 6/2 Complex  Millmar | A | 0.01 | 0.01 | Lightning | Lightning | Lightning | Lightning | nan | 42.68361 | -122.42444 | POINT (-122.42444 42.68361) | Industrial | 33S | 03E | 23.0 | NESE | 12 miles NE of Butte Falls | Jackson | SW2 | Outside Closed Fire Season | Outside Closed Fire Season | 2007 Jun 02 01:00:00 AM | 2007 Jun 02 10:00:00 AM | 2007 Jun 02 09:50:00 AM | 2007 Jun 02 01:00:00 PM | 2007 Jun 04 10:21:00 AM | 2007 Oct 15 01:14:00 PM | 71 | 711 | 168 | portal_sci_data_ics209_demo |
| 77887 | STAT | 2007 | SOA | Southwest Oregon | Medford | 07-711030-08 | 7/10 Complex | 7/10 Complex Hyatt Lake | A | 0.01 | 0.01 | Lightning | Lightning | Lightning | Lightning | nan | 42.18639 | -122.45667 | POINT (-122.45667 42.18639) | BLM | 39S | 03E | 10.0 | SESW | 13 Mi E of Ashland | Jackson | SW2 | Reg Use Closure | Lvl 1 Fire Season Only | 2007 Jul 10 10:00:00 PM | 2007 Jul 10 10:19:00 PM | 2007 Jul 10 10:15:00 PM | 2007 Jul 10 11:00:00 PM | 2007 Jul 13 12:00:00 AM | 2007 Jul 21 01:04:00 PM | 71 | 711 | 30 | portal_sci_data_ics209_demo |
| 81830 | STAT | 2008 | SOA | Southwest Oregon | Medford | 08-711058-09 | 8/16 Complex | 8/16 Complex | A | 0.1 | 0.0 | Lightning | Lightning | Lightning | Lightning | nan | 42.68694 | -122.39528 | POINT (-122.39528 42.68694) | USFS | 33S | 04E | 19.0 | SENW | 13 Miles NE of Butte Falls | Jackson | RR1 | Reg Use Closure | Lvl 2 Limited Shutdown | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 04:37:00 PM | 2008 Aug 16 07:39:00 PM | 2008 Aug 16 12:00:00 AM | 2008 Dec 16 02:37:00 PM | 71 | 711 | 58 | portal_sci_data_ics209_demo |
| 82745 | STAT | 2008 | SOA | Southwest Oregon | Medford | 08-711106-09 | 9/16 Complex | 9/16 Complex | A | 0.01 | 0.01 | Human | Timber Harvest Worker | Equipment Use | Other -Equipment Use Related (ie. road const., other i.c.e.) | Hot Saw | 42.61139 | -122.49778 | POINT (-122.49778 42.61139) | Industrial | 34S | 03E | 17.0 | NWSW | 10 Mi SE of Butte Falls | Jackson | SW2 | Reg Use Closure | Lvl 2 Limited Shutdown | 2008 Sep 16 04:00:00 PM | 2008 Sep 16 08:03:00 PM | 2008 Sep 16 08:03:00 PM | 2008 Sep 16 10:18:00 PM | 2008 Sep 17 12:00:00 AM | 2008 Sep 24 09:25:00 AM | 71 | 711 | 106 | portal_sci_data_ics209_demo |
| 143654 | STAT | 2025 | SOA | SWO | Medford | 25-711053-26 | Eastside Lightning Complex | Heppsie | D | 110.11 | 110.11 | Lightning | Lightning | Lightning | Lightning | Lightning caused fire | 42.38433 | -122.49767 | POINT (-122.49767 42.38433) | BLM | 37S | 3E | 5.0 | SENW | Heppsie Mountain | Jackson | SW2 | Reg Use Closure | Lvl 2 Limited Shutdown | 2025-07-07T18:41:00.000 | 2025-07-07T20:58:00.000 | 2025-07-07T20:58:00.000 | 2025-10-11T14:00:00.000 | 2025-07-07T00:00:00.000 | 2025-10-13T14:37:00.000 | 71 | 711 | 053 | portal_sci_data_ics209_demo |

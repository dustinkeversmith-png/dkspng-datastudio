# Data Identity Card: nifc_northwest_incidents

## Source Lineage
- **URL**: local://nifc_northwest_incidents.csv
- **Fetched At**: 2026-05-16T02:57:13.552087
- **Patch Row Count**: 16

## Column Index
| Column Name | Inferred Type | Unit/Tag | Nulls | Unique | Description |
|-------------|---------------|----------|-------|--------|-------------|
| OBJECTID | numeric | - | 0 | 16 | - |
| SourceOID | numeric | - | 0 | 16 | - |
| ABCDMisc | numeric | - | 0 | 16 | - |
| ADSPermissionState | categorical | label_lookup | 0 | 1 | - |
| ContainmentDateTime | numeric | - | 0 | 16 | - |
| ControlDateTime | numeric | - | 0 | 16 | - |
| CreatedBySystem | string | - | 0 | 3 | - |
| IncidentSize | numeric | - | 0 | 15 | - |
| DiscoveryAcres | numeric | - | 0 | 11 | - |
| DispatchCenterID | string | - | 0 | 5 | - |
| EstimatedCostToDate | currency | USD | 0 | 16 | - |
| FinalAcres | numeric | - | 0 | 16 | - |
| FinalFireReportApprovedByTitle | numeric | - | 0 | 16 | - |
| FinalFireReportApprovedByUnit | numeric | - | 0 | 16 | - |
| FinalFireReportApprovedDate | numeric | - | 0 | 16 | - |
| FireBehaviorGeneral | numeric | - | 0 | 16 | - |
| FireBehaviorGeneral1 | numeric | - | 0 | 16 | - |
| FireBehaviorGeneral2 | numeric | - | 0 | 16 | - |
| FireBehaviorGeneral3 | numeric | - | 0 | 16 | - |
| FireCause | string | - | 0 | 4 | - |
| FireCauseGeneral | numeric | - | 0 | 16 | - |
| FireCauseSpecific | numeric | - | 0 | 16 | - |
| FireCode | string | - | 0 | 11 | - |
| FireDepartmentID | numeric | - | 0 | 16 | - |
| FireDiscoveryDateTime | numeric | - | 0 | 16 | - |
| FireMgmtComplexity | numeric | - | 0 | 16 | - |
| FireOutDateTime | numeric | - | 0 | 16 | - |
| FireStrategyConfinePercent | numeric | - | 0 | 16 | - |
| FireStrategyFullSuppPercent | numeric | - | 0 | 16 | - |
| FireStrategyMonitorPercent | numeric | - | 0 | 16 | - |
| FireStrategyPointZonePercent | numeric | - | 0 | 16 | - |
| FSJobCode | numeric | - | 0 | 16 | - |
| FSOverrideCode | numeric | - | 0 | 16 | - |
| GACC | string | - | 0 | 2 | Geographic Area Coordination Center region |
| ICS209ReportDateTime | numeric | - | 0 | 16 | - |
| ICS209ReportForTimePeriodFrom | numeric | - | 0 | 16 | - |
| ICS209ReportForTimePeriodTo | numeric | - | 0 | 16 | - |
| ICS209ReportStatus | string | - | 0 | 2 | - |
| IncidentManagementOrganization | numeric | - | 0 | 16 | - |
| IncidentName | string | - | 0 | 16 | - |
| IncidentShortDescription | numeric | - | 0 | 16 | - |
| IncidentTypeCategory | string | - | 0 | 2 | - |
| IncidentTypeKind | categorical | label_lookup | 0 | 1 | - |
| InitialLatitude | float | decimal_degrees | 0 | 16 | - |
| InitialLongitude | float | decimal_degrees | 0 | 16 | - |
| InitialResponseAcres | numeric | - | 0 | 16 | - |
| InitialResponseDateTime | numeric | - | 0 | 16 | - |
| IrwinID | string | - | 0 | 16 | - |
| IsFireCauseInvestigated | numeric | - | 0 | 16 | - |
| IsFireCodeRequested | categorical | label_lookup | 0 | 1 | - |
| IsFSAssisted | numeric | - | 0 | 3 | - |
| IsMultiJurisdictional | numeric | - | 0 | 4 | - |
| IsQuarantined | categorical | label_lookup | 0 | 1 | - |
| IsReimbursable | numeric | - | 0 | 5 | - |
| IsTrespass | numeric | - | 0 | 4 | - |
| IsUnifiedCommand | numeric | - | 0 | 16 | - |
| IsValid | categorical | label_lookup | 0 | 1 | - |
| LocalIncidentIdentifier | numeric | - | 0 | 16 | - |
| PercentContained | numeric | - | 0 | 16 | - |
| PercentPerimeterToBeContained | numeric | - | 0 | 16 | - |
| POOCity | numeric | - | 0 | 16 | - |
| POOCounty | string | - | 0 | 4 | - |
| POODispatchCenterID | string | - | 0 | 6 | - |
| POOFips | numeric | - | 0 | 4 | - |
| POOJurisdictionalAgency | string | - | 0 | 5 | - |
| POOJurisdictionalUnit | string | - | 0 | 7 | - |
| POOJurisdictionalUnitParentUnit | numeric | - | 0 | 16 | - |
| POOLandownerCategory | string | - | 0 | 4 | - |
| POOLandownerKind | string | - | 0 | 3 | - |
| POOLegalDescPrincipalMeridian | numeric | - | 0 | 16 | - |
| POOLegalDescQtr | numeric | - | 0 | 16 | - |
| POOLegalDescQtrQtr | numeric | - | 0 | 16 | - |
| POOLegalDescRange | numeric | - | 0 | 16 | - |
| POOLegalDescSection | numeric | - | 0 | 16 | - |
| POOLegalDescTownship | numeric | - | 0 | 16 | - |
| POOPredictiveServiceAreaID | numeric | area | 0 | 4 | - |
| POOProtectingAgency | string | - | 0 | 5 | - |
| POOProtectingUnit | string | - | 0 | 7 | - |
| POOState | string | - | 0 | 2 | - |
| PredominantFuelGroup | numeric | - | 0 | 16 | - |
| PredominantFuelModel | numeric | - | 0 | 16 | - |
| PrimaryFuelModel | numeric | - | 0 | 16 | - |
| SecondaryFuelModel | numeric | - | 0 | 16 | - |
| TotalIncidentPersonnel | numeric | - | 0 | 16 | - |
| UniqueFireIdentifier | string | - | 0 | 16 | - |
| WFDSSDecisionStatus | categorical | label_lookup | 0 | 1 | - |
| EstimatedFinalCost | currency | USD | 0 | 16 | - |
| OrganizationalAssessment | numeric | - | 0 | 16 | - |
| StrategicDecisionPublishDate | numeric | - | 0 | 16 | - |
| CreatedOnDateTime_dt | numeric | - | 0 | 16 | - |
| ModifiedOnDateTime_dt | numeric | - | 0 | 16 | - |
| IsCpxChild | categorical | label_lookup | 0 | 1 | - |
| CpxName | numeric | - | 0 | 16 | - |
| CpxID | numeric | - | 0 | 16 | - |
| SourceGlobalID | string | - | 0 | 16 | - |
| GlobalID | string | - | 0 | 16 | - |
| IncidentComplexityLevel | numeric | - | 0 | 16 | - |
| longitude | float | decimal_degrees | 0 | 16 | - |
| latitude | float | decimal_degrees | 0 | 16 | - |
| session_source_key | categorical | label_lookup | 0 | 1 | - |

## Data Sample (Top 5 Rows)
| OBJECTID | SourceOID | ABCDMisc | ADSPermissionState | ContainmentDateTime | ControlDateTime | CreatedBySystem | IncidentSize | DiscoveryAcres | DispatchCenterID | EstimatedCostToDate | FinalAcres | FinalFireReportApprovedByTitle | FinalFireReportApprovedByUnit | FinalFireReportApprovedDate | FireBehaviorGeneral | FireBehaviorGeneral1 | FireBehaviorGeneral2 | FireBehaviorGeneral3 | FireCause | FireCauseGeneral | FireCauseSpecific | FireCode | FireDepartmentID | FireDiscoveryDateTime | FireMgmtComplexity | FireOutDateTime | FireStrategyConfinePercent | FireStrategyFullSuppPercent | FireStrategyMonitorPercent | FireStrategyPointZonePercent | FSJobCode | FSOverrideCode | GACC | ICS209ReportDateTime | ICS209ReportForTimePeriodFrom | ICS209ReportForTimePeriodTo | ICS209ReportStatus | IncidentManagementOrganization | IncidentName | IncidentShortDescription | IncidentTypeCategory | IncidentTypeKind | InitialLatitude | InitialLongitude | InitialResponseAcres | InitialResponseDateTime | IrwinID | IsFireCauseInvestigated | IsFireCodeRequested | IsFSAssisted | IsMultiJurisdictional | IsQuarantined | IsReimbursable | IsTrespass | IsUnifiedCommand | IsValid | LocalIncidentIdentifier | PercentContained | PercentPerimeterToBeContained | POOCity | POOCounty | POODispatchCenterID | POOFips | POOJurisdictionalAgency | POOJurisdictionalUnit | POOJurisdictionalUnitParentUnit | POOLandownerCategory | POOLandownerKind | POOLegalDescPrincipalMeridian | POOLegalDescQtr | POOLegalDescQtrQtr | POOLegalDescRange | POOLegalDescSection | POOLegalDescTownship | POOPredictiveServiceAreaID | POOProtectingAgency | POOProtectingUnit | POOState | PredominantFuelGroup | PredominantFuelModel | PrimaryFuelModel | SecondaryFuelModel | TotalIncidentPersonnel | UniqueFireIdentifier | WFDSSDecisionStatus | EstimatedFinalCost | OrganizationalAssessment | StrategicDecisionPublishDate | CreatedOnDateTime_dt | ModifiedOnDateTime_dt | IsCpxChild | CpxName | CpxID | SourceGlobalID | GlobalID | IncidentComplexityLevel | longitude | latitude | session_source_key |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 22 | 6808381 | nan | DEFAULT | nan | nan | cfcad | nan | 0.1 | CAYICC | nan | nan | nan | nan | nan | nan | nan | nan | nan | Unknown | nan | nan | MQ6D | nan | 1567701591000 | nan | nan | nan | nan | nan | nan | nan | nan | ONCC | nan | nan | nan | nan | nan | MARTIN 2 | nan | WF | FI | 41.716768 | -122.34566 | nan | nan | {9D6CFD63-6044-497A-9C92-F6B0599BEC17} | nan | 0 | 1.0 | nan | 0 | nan | nan | nan | 1 | 7067 | nan | nan | nan | Siskiyou | CAYICC | 6093 | nan | CASKU | nan | nan | nan | nan | nan | nan | nan | nan | nan | NC06 | nan | CASKU | US-CA | nan | nan | nan | nan | nan | 2019-CASKU-007067 | No Decision | nan | nan | nan | 1567701596470 | 1567702241707 | 0 | nan | nan | {9D6CFD63-6044-497A-9C92-F6B0599BEC17} | 7612d798-b47d-4071-a073-ae4b1b7c763c | nan | -122.34565999999997 | 41.71676800000006 | nifc_wildfire_incidents |
| 92 | 3192631 | nan | DEFAULT | nan | nan | firecode | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | K3F9 | nan | 1498764180000 | nan | nan | nan | nan | nan | nan | nan | nan | ONCC | nan | nan | nan | nan | nan | MACDOEL | nan | WF | FI | nan | nan | nan | nan | {01F76FFC-8F56-456A-8A49-6B1E6F7191D5} | nan | 0 | 1.0 | 0.0 | 0 | 1.0 | 0.0 | nan | 1 | 4609 | nan | nan | nan | Siskiyou | nan | 6093 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | NC06 | CDF | CASKU | US-CA | nan | nan | nan | nan | nan | 2017-CASKU-004609 | No Decision | nan | nan | nan | 1498764796993 | 1498764796993 | 0 | nan | nan | {01F76FFC-8F56-456A-8A49-6B1E6F7191D5} | 8d231d94-ec5c-4e12-91f7-6f989cbc3464 | nan | -121.93527777999998 | 41.83638889000008 | nifc_wildfire_incidents |
| 345 | 3915682 | nan | DEFAULT | nan | nan | wildcad | 0.1 | 0.1 | ORLFC | nan | nan | nan | nan | nan | nan | nan | nan | nan | Undetermined | nan | nan | nan | nan | 1522170433000 | nan | nan | nan | nan | nan | nan | nan | nan | NWCC | nan | nan | nan | nan | nan | Pilot RX | nan | RX | FI | 42.46247 | -120.9291 | nan | nan | {5FEA6750-3CC0-4A99-94B0-B618E8A75EBD} | nan | 0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | nan | 1 | 12 | nan | nan | nan | Klamath | nan | 41035 | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | NW07 | FS | ORFWF | US-OR | nan | nan | nan | nan | nan | 2018-ORFWF-000012 | No Decision | nan | nan | nan | 1522192733227 | 1522192733227 | 0 | nan | nan | {5FEA6750-3CC0-4A99-94B0-B618E8A75EBD} | e3e16e24-b3fa-4448-b8af-b14d5493c283 | nan | -120.92909999999996 | 42.46247000000005 | nifc_wildfire_incidents |
| 351 | 7233178 | nan | DEFAULT | nan | nan | wildcad | nan | nan | ORRVC | nan | nan | nan | nan | nan | nan | nan | nan | nan | Unknown | nan | nan | nan | nan | 1573170948000 | nan | nan | nan | nan | nan | nan | nan | nan | NWCC | nan | nan | nan | nan | nan | HC Corridor Clean Up | nan | RX | FI | 42.46848 | -122.4328 | nan | nan | {31798E58-17D0-40FC-AB7E-0A7AF8CF1A82} | nan | 0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | nan | 1 | 560 | nan | nan | nan | Jackson | ORRVC | 41029 | FS | ORRSF | nan | nan | nan | nan | nan | nan | nan | nan | nan | NW04 | FS | ORRSF | US-OR | nan | nan | nan | nan | nan | 2019-ORRSF-000560 | No Decision | nan | nan | nan | 1573174723300 | 1573230535787 | 0 | nan | nan | {31798E58-17D0-40FC-AB7E-0A7AF8CF1A82} | d07e76dc-8cdc-4c61-8849-3aa1e47bfee4 | nan | -122.4328 | 42.468480000000056 | nifc_wildfire_incidents |
| 369 | 7504378 | nan | DEFAULT | nan | nan | wildcad | nan | nan | ORRVC | nan | nan | nan | nan | nan | nan | nan | nan | nan | Unknown | nan | nan | nan | nan | 1556920421000 | nan | nan | nan | nan | nan | nan | nan | nan | NWCC | nan | nan | nan | nan | nan | BF Double Bowen Unit 7-1 | nan | RX | FI | 42.53936 | -122.513 | nan | nan | {FC8C56DD-7B17-4DBB-9D42-AC64E1B1F7D4} | nan | 0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | nan | 1 | 71 | nan | nan | nan | Jackson | ORRVC | 41029 | BLM | ORMED | nan | nan | nan | nan | nan | nan | nan | nan | nan | NW04 | BLM | ORMED | US-OR | nan | nan | nan | nan | nan | 2019-ORMED-000071 | No Decision | nan | nan | nan | 1576681875563 | 1605893651010 | 0 | nan | nan | {FC8C56DD-7B17-4DBB-9D42-AC64E1B1F7D4} | be54dc65-1eb1-4cb2-ae49-35fca95b495a | nan | -122.51299999999998 | 42.539360000000045 | nifc_wildfire_incidents |

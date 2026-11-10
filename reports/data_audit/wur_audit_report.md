# WUR 2018 Dataset Audit

## 1. Dataset provenance

- **Dataset:** Autonomous Greenhouse Challenge First Edition 2018.
- **DOI:** [10.4121/uuid](https://doi.org/10.4121/uuid\:e4987a7b-04dd-4c89-9b18-883aad30ba9a)
- **WUR source URL:** [https://research.wur.nl/en/datasets/autonomous-greenhouse-challenge-first-edition-2018/](https://research.wur.nl/en/datasets/autonomous-greenhouse-challenge-first-edition-2018/)
- **4TU.ResearchData deposit:** [https://data.4tu.nl/datasets/c362564b-bc9e-40ec-856b-b616bb909183/1](https://data.4tu.nl/datasets/c362564b-bc9e-40ec-856b-b616bb909183/1)
- **Download date:** Not yet recorded. Fill in the actual date from the download record; do not infer it from the audit date.
- **Publisher:** Wageningen University & Research (WUR).
- **Crop:** Cucumber, cultivar Hi Power.
- **Location:** Bleiswijk, Netherlands.
- **Temporal coverage:** August–December 2018.
- **License:** CC0 1.0 Universal (Public Domain Dedication), SPDX `CC0-1.0`, verified against the dataset-specific 4TU deposit.
- **Citation:** Wageningen University & Research. *Autonomous Greenhouse Challenge First Edition 2018*. Dataset. DOI: 10.4121/uuid.
- **License note:** CC0 does not require attribution as a license condition, but academic citation of the original dataset is recommended.

## 2. Dataset integrity

- **Original archive:** `data.zip`, reported source archive size 8,975,944 bytes. The accompanying `ReadMe.pdf` is 36,355 bytes in the source deposit.
- **Number of locally extracted files:** 38 files:
  - 37 CSV files.
  - 1 PDF file (`ReadMe.pdf`).
- **Number of team directories:** 6.
- **Total size of locally extracted dataset files:** 41,625,275 bytes.
- **SHA-256 verification:** 38 extracted files were included in `metadata/wur_sha256.txt`; all 38 passed `sha256sum --check`.
- **Integrity scope:** The verified manifest covers the extracted files, not the original `data.zip` archive. An archive-level checksum has not been established.
- **Original data preservation:** Raw files are kept under `data/raw/wur/` and excluded from Git tracking. Audit scripts read the source files without modifying them.

## 3. Dataset structure

- **Root directory:** `data/raw/wur/`
- **Team directories:**
  - `AiCU/`
  - `Croperators/`
  - `DeepGreens/`
  - `iGrow/`
  - `Reference(Growers)/`
  - `Sonoma/`
- **Files in each team directory:**
  - `CropManagement.csv`
  - `Greenhouse_climate.csv`
  - `Irrigation.csv`
  - `Production.csv`
  - `ResourceCalculations.csv`
  - `vip.csv`
- **Root-level files:**
  - `meteo.csv`
  - `ReadMe.pdf`
- **File formats:** CSV and PDF.
- **Tables / worksheets:** 37 CSV tables and one PDF documentation file. No Excel workbook or worksheet structure was identified.
- **Inventory:** Six team directories, each containing six CSV files, plus one root-level weather CSV and one README PDF.

## 4. Temporal coverage

- **Earliest greenhouse climate timestamp:** 2018-08-14 00:00:00.
- **Latest greenhouse climate timestamp:** 2018-12-07 01:00:00.
- **Climate observations:** 33,133 unique timestamps per team.
- **Daily production observations:** 116 unique dates per team, from 2018-08-14 through 2018-12-07.
- **Documented sampling frequencies:**
  - Weather station (`meteo.csv`): 5 minutes.
  - Greenhouse climate: 5 minutes.
  - VIP control setpoints: 5 minutes.
  - Irrigation: daily.
  - Resource calculations: daily.
  - Production: daily.
  - Crop management: weekly.
- **Missing climate timestamps:** Zero missing five-minute timestamps per team after normalizing Excel serial timestamp precision.
- **Missing daily production dates:** Zero missing dates in the observed production period per team.
- **Duplicate timestamps:** No duplicate timestamps were detected in the audited timestamp-bearing CSV files.
- **Timestamp handling:** Climate timestamps were rounded to the documented five-minute resolution before continuity checks to avoid false gaps caused by Excel floating-point precision.

## 5. Greenhouse compartments

- **Expected experimental groups:** 6.
- **Actual directories:** 6.
- **Directory names:** AiCU, Croperators, DeepGreens, iGrow, Reference(Growers), Sonoma.
- **Experimental context:** Five AI teams and one manually operated Reference compartment.
- **Physical compartment IDs:** Not established from the audited files and README.
- **Missing experimental groups:** None at the directory level.
- **Important limitation:** The six team directories represent six experimental groups, but their exact mapping to physical greenhouse compartment identifiers has not been verified. Do not invent physical compartment IDs from directory names.

## 6. Available variables

### Climate

Greenhouse climate variables, documented at five-minute intervals:

- `Tair`: greenhouse air temperature (°C).
- `RHair`: greenhouse relative humidity (%).
- `CO2air`: greenhouse CO₂ concentration (ppm).
- `HumDef`: humidity deficit (g/m³).
- `VentLee`: lee-side ventilation (%).
- `Ventwind`: wind-side ventilation (%).
- `AssimLight`: assimilation lighting (%).
- `EnScr`: energy curtain position (%).
- `BlackScr`: black-out curtain position (%).
- `PipeLow`: lower circuit temperature (°C).
- `PipeGrow`: growth circuit temperature (°C).

The root-level `meteo.csv` contains outside weather variables, including temperature, humidity, radiation, wind, rain, PAR, and absolute humidity.

### Irrigation

Daily variables:

- `Water`: irrigation water supplied (L/m²).
- `Drain`: drainage water (L/m²).
- `pH_Drain`: drainage pH.
- `EC_Drain`: drainage electrical conductivity (dS/m).

The README describes pH and EC as daily averages of five-minute probe data. Its explanatory comment for `Water` is ambiguous and needs clarification.

### Control

The `vip.csv` files contain five-minute control setpoints, including:

- CO₂ setpoint.
- Humidity deficit setpoint.
- Minimum pipe temperature setpoints.
- Heating temperature setpoint.
- Lee-side and wind-side ventilation temperature setpoints.
- Minimum lee-side window position.
- Water supply interval time setpoint.

The five non-AiCU teams have 10 VIP columns each. AiCU has 35 columns: one timestamp and 30 indexed control columns. The README documents the underlying control-variable families but does not explain the AiCU index suffixes.

### Cultivation

Weekly crop-management variables include:

- Fruit maintained on internode (%).
- Leaves maintained on internode (%).
- Stem elongation (cm/week).
- Fruit development time (days/fruit).
- Leaf formation rate (leaves/stem/week).
- Cumulative number of leaves (leaves/stem).
- Week number.

### Resources

Daily processed variables include:

- Heating energy consumption (kWh/m²/day).
- Artificial lighting electricity consumption (kWh/m²/day).
- CO₂ consumption (kg/m²/day).
- Net water use (L/m²/day).
- Labour hours (hours/day).

The README describes `net_water` as irrigation minus drainage. Other resource variables are also calculated from underlying operating information rather than all being independent raw measurements.

### Yield / production

Daily manually registered production variables include:

- `ProdA_cum`: cumulative category A cucumber production (kg/m²).
- `ProdB_cum`: cumulative category B cucumber production (kg/m²).
- `Total_Prod_cum`: total cumulative production (kg/m²).
- `ProdA_num`: documented cumulative number of category A cucumbers.
- `ProdB_num`: documented cumulative number of category B cucumbers.
- `Prod_value_cum`: production value (€).

## 7. Harvest and yield analysis

- **Harvest records:** 116 daily production observations per experimental group.
- **Harvest timestamps:** Daily timestamps from 2018-08-14 through 2018-12-07.
- **Registration method:** The README identifies production as processed data from manual registration.
- **Yield variables:** `ProdA_cum`, `ProdB_cum`, and `Total_Prod_cum`.
- **Yield units:** kg/m².
- **Production per experimental group:** All six groups have 116 production observations. Their cumulative production values are present in the production tables; a comparative final-yield summary has not yet been generated as a dedicated report.
- **Production consistency:** `Total_Prod_cum = ProdA_cum + ProdB_cum` holds for all 696 observations (116 × 6).
- **Cumulative behavior:** The three cumulative mass variables are non-decreasing, apart from negligible floating-point noise in one Reference observation.
- **Candidate forecasting target:** Daily increment of total cumulative production:

  `daily_yield_t = Total_Prod_cum_t - Total_Prod_cum_(t-1)`

  The resulting target has units of kg/m²/day.
- **Alternative targets:** Daily increments of `ProdA_cum` and `ProdB_cum`.
- **First observation:** The first daily increment is undefined because no preceding cumulative observation exists.
- **Fruit-count discrepancy:** The README documents `ProdA_num` and `ProdB_num` as cumulative fruit counts, but the audit observed fractional values and decreases. Their numerical behavior conflicts with the documented semantics. They should not be reclassified as interval counts without further evidence.

## 8. Limitations

### Missing variables and schema differences

- `BlackScr` is 100% missing in DeepGreens.
- AiCU's VIP schema differs from the other five teams.
- AiCU contains indexed VIP variables whose index semantics are not documented.
- The cause of the missing DeepGreens `BlackScr` values is unknown.

### Missing observations

- Greenhouse climate variables generally have approximately 0.43% missing values per affected column.
- `CO2_Vip` and `WaterSupInt_Vip` in the non-AiCU VIP files have approximately 1.75% missing values.
- AiCU has additional missing VIP values, including a completely missing `HeatTemp_Vip_4` column.
- Crop-management files contain missing values; Reference(Growers) has more missing cells than the other groups.
- Irrigation has one missing `Water` and one missing `Drain` observation per group.
- Resource calculations have one missing `net_water` observation per group.
- Production files have no missing values in the audited production records.

### Irregular sampling

- No missing five-minute climate timestamps were detected after timestamp normalization.
- No missing daily production dates were detected.
- No duplicate timestamps were detected in the audited files.
- The dataset nevertheless combines five-minute, daily, and weekly measurements. These require explicit temporal alignment for modeling.

### Unresolved questions

1. What are the physical greenhouse compartment IDs corresponding to the six experimental groups?
2. What do the AiCU VIP indices represent?
3. Why do `ProdA_num` and `ProdB_num`, documented as cumulative counts, contain fractional values and decreases?
4. Why is `BlackScr` entirely missing in DeepGreens?
5. What exactly does the README mean by the `Water` comment about the time between irrigation turns?
6. What is the intended unit for `Winddir`, printed as `0-360?` in the README?
7. Are there additional dataset documents explaining team-to-compartment mapping and control-variable indexing?

### Modeling limitations

- The dataset covers one greenhouse challenge season of approximately four months.
- There are six experimental groups, not hundreds of independent greenhouse environments.
- High-frequency measurements are repeated observations within those groups and must not be treated as independent experimental units.
- The WUR dataset does not establish paired RGB imagery for the audited sensor and production observations.
- Daily production labels and five-minute input variables require a carefully defined forecasting horizon, aggregation procedure, and leakage-safe temporal alignment.

## 9. Conclusion

- **Dataset usable for forecasting:** CONDITIONAL — suitable for initial single-season, six-group greenhouse yield forecasting experiments, subject to careful validation and explicit limitations.
- **Reason:**
  - The dataset has documented climate, control, irrigation, cultivation, resource, and production variables.
  - Daily production records are complete over the observed period.
  - Cumulative mass variables have documented units and pass internal consistency checks.
  - Climate timestamps are continuous at the documented five-minute resolution.
  - Important schema and semantic issues remain, but they are identifiable and can be documented.
- **Recommended next steps:**
  1. Generate a per-group final cumulative production summary.
  2. Investigate the fruit-count variable discrepancy.
  3. Investigate AiCU VIP indexing and DeepGreens `BlackScr` missingness.
  4. Establish the team-to-physical-compartment mapping if supporting documentation is available.
  5. Define the forecasting target, prediction horizon, temporal aggregation, and leakage-safe split strategy.
  6. Preserve the data dictionary, audit reports, metadata, and checksum manifest alongside the research code.

---

## Audit artifacts

- `metadata/wur_metadata.json`
- `metadata/wur_sha256.txt`
- `metadata/wur_data_dictionary.csv`
- `reports/data_audit/wur_file_tree.txt`
- `reports/data_audit/wur_quality_report.txt`
- `reports/data_audit/wur_value_inspection.txt`
- `reports/data_audit/wur_readme_audit_comparison.md`
- `scripts/data_audit/wur_quality_audit.py`
- `scripts/data_audit/wur_value_inspection.py`
- `scripts/data_audit/build_wur_data_dictionary.py`

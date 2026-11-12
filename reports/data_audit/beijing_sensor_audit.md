# Beijing 2024–2025 Greenhouse Sensor Dataset Audit

**Document:** Comprehensive Data Quality, Sensor Characterization, and Research Usability Audit  
**Dataset:** 2024−2025 Dataset of Air and Soil Temperature and Humidity for Greenhouse-Grown Vegetables in Beijing  
**Chinese Title:** 2024-2025年北京设施蔬菜空气与土壤温湿度数据集  
**Repository:** `vtrnnhlinh/POLAR-Cuke` (Issue #7)  
**Audit Date:** November 2026  
**Auditor:** POLAR-Cuke Research Team  

---

## Executive Summary

This report delivers a rigorous audit of the Beijing 2024–2025 Greenhouse Sensor Dataset deposited on Science Data Bank (ScienceDB, DOI: `10.57760/sciencedb.agriculture.00283`). The audit evaluates dataset provenance, file integrity, sensor instrumentation, temporal continuity, empirical sampling intervals, missingness patterns, sentinel error codes, crop phenology, and harvest/yield label availability.

### Key Audit Findings

1. **Yield-Label Status & Decision Rule:**
   - **Harvest weights, fruit counts, cumulative yields, and economic returns are entirely absent** from all tables and worksheets.
   - While phenological stage date intervals are recorded in the `生育期` (Growth Stages) sheet, no numerical production target can be established.
   - **Mandatory Decision Rule Enforcement:** In accordance with the project specification, **this dataset must not be used to train, evaluate, or report external cucumber yield forecasting performance.**
2. **Sensor Pretraining & Transfer Usability:**
   - The dataset provides **151,109 raw sensor records** (95,654 air observations + 55,455 soil observations) across four vegetable cultivation seasons, including **60,450 records for cucumber** (*Cucumis sativus L.*, cv. ‘中农26号’).
   - The cucumber dataset demonstrates exceptional temporal continuity (zero gaps > 1h in soil; only two short gaps ~1.2h in air).
   - This makes the dataset highly valuable for **sensor representation pretraining**, **cross-climate distribution-shift evaluation**, and **domain adaptation** between Chinese solar greenhouses and European/Korean glasshouses (WUR and RDA).
3. **Critical Empirical Quality Discoveries:**
   - **Unmasked Sentinel Error Codes:** The DZN2 soil moisture probe channels intermittently record `-1000.0` during communication or hardware dropouts (27 records in Autumn Tomato; 140 records across depths in Cucumber). These unmasked sentinels drastically distort statistical moments (inflating cucumber 40cm moisture standard deviation from 1.90% to 54.77%) and must be masked prior to model training.
   - **Diurnal Logging in Fast Cabbage:** The Greenhouse Doll II air sensor for fast cabbage was powered down nightly, resulting in a persistent ~17-hour nighttime blackout (17:00–10:00) every day.
   - **Empirical Sampling Rate Discrepancies:** While documentation claims a uniform 15-minute soil sampling rate, Spring Tomato soil is sampled at 5-minute intervals (with 1–2s drift), and Cucumber soil transitions dynamically from 15-minute to 5-minute sampling on April 18, 2025.
   - **Hardware Outages in Autumn Tomato:** Autumn Tomato soil monitoring experienced multi-day outages spanning 9.51 days, 17.39 days, and 6.01 days.

---

## 1. Dataset Provenance & Access Conditions

### 1.1 Citation and Repository Identifiers

- **Dataset Title:** 2024−2025 Dataset of Air and Soil Temperature and Humidity for Greenhouse-Grown Vegetables in Beijing
- **Chinese Title:** 2024-2025年北京设施蔬菜空气与土壤温湿度数据集
- **DOI:** [10.57760/sciencedb.agriculture.00283](https://doi.org/10.57760/sciencedb.agriculture.00283)
- **Data Repository:** Science Data Bank (ScienceDB, [https://www.scidb.cn](https://www.scidb.cn))
- **ScienceDB Dataset ID:** `30ed918efdfa4c6385a0cd7e33bce7a9`
- **Dataset Version:** V1 (Published: 2025-12-22)
- **Croissant / Schema.org Conformance:** Conforms to MLCommons Croissant 1.0 specification.
- **Formal Academic Citation:**
  > Zhang Shirui, Jia Yuxuan, Li Youli, Guo Yuanyuan, Qu Mingshan, Zhang Xin. *2024−2025 Dataset of Air and Soil Temperature and Humidity for Greenhouse-Grown Vegetables in Beijing*. Science Data Bank, 2025. DOI: `10.57760/sciencedb.agriculture.00283`.

### 1.2 Contributing Institutions & Authors

The dataset was generated collaboratively by four Chinese agricultural research and extension organizations:
1. **Intelligent Equipment Research Center, Beijing Academy of Agriculture and Forestry Sciences (北京市农林科学院智能装备技术研究中心):** Zhang Shirui, Li Youli, Zhang Xin.
2. **Shanxi Agricultural University (山西农业大学, ROR: `https://ror.org/05e9f5362`):** Jia Yuxuan.
3. **Nongxin Technology (Beijing) Co., Ltd. (农芯科技(北京)有限责任公司):** Guo Yuanyuan.
4. **Beijing Agricultural Technology Extension Station (北京市农业技术推广站):** Qu Mingshan.

### 1.3 Geographic Location & Greenhouse Characteristics

- **Experimental Facility:** Beijing Xiaotangshan National Precision Agriculture Research and Demonstration Base (北京小汤山国家精准农业研究示范基地).
- **Coordinates:** Latitude 40.180366°N, Longitude 116.450659°E (Changping District, Beijing, China).
- **Greenhouse Architecture:** Two adjacent Chinese solar greenhouses (砖墙日光温室, passive solar design with thermal mass brick back-walls) having identical physical structures.
- **Geometric Dimensions:**
  - Total greenhouse length: 50.0 m (effective cultivation length: 46.7 m).
  - Greenhouse width (span): 7.0 m.
  - Total ground area: 350.0 m² (effective cultivation bed area: 326.9 m²).
  - North back-wall height: 2.5 m (brick heat-storage structure).
  - Ridge height: 3.7 m.
- **Agronomic Layout:** East-West ridge soil cultivation (东西垄土壤种植), containing 4 longitudinal ridges, each 46.7 m long.
- **Sensor Placement:** The sensor cluster is installed in the center of the 2nd cultivation ridge at the geometric center of the greenhouse compartment.

### 1.4 Licensing Terms & Research Use

- **License:** Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (`CC BY-NC-ND 4.0`).
- **Permitted Research Use:** Non-commercial academic research, exploratory data analysis, and model training are permitted provided proper attribution is given.
- **Distribution Restrictions:** The `NoDerivatives` (ND) clause prohibits publicly distributing modified, transformed, or remixed versions of the raw data tables. Feature extraction, internal embeddings, and trained model weights do not constitute derivative datasets under standard copyright law, but cleaned data tables must not be redistributed externally.

---

## 2. Dataset Integrity & File Inventory

### 2.1 Local File Verification

The raw dataset comprises four Microsoft Excel (`.xlsx`) workbooks totaling 4,814,747 bytes. All files were copied to `data/raw/beijing/` (git-ignored) and verified against `metadata/beijing_sha256.txt`.

| File Name | Crop / Cultivar | File Size (Bytes) | SHA-256 Checksum | Integrity Status |
| :--- | :--- | :---: | :---: | :---: |
| `温室黄瓜种植监测数据（2025年3月6日~2025年7月3日）.xlsx` | Cucumber (*Zhongnong No. 26*) | 1,899,396 | `5aec2edacfeee1916b73dcd63b87d0a9382231f40eac53300edda35c926e537a` | **PASS** |
| `温室春茬番茄种植监测数据（2024年5月1日~2025年7月10日）.xlsx` | Spring Tomato (*Jingcai No. 8*) | 1,205,613 | `3f119bf4b2a13f8675394b0c09ce2afd570ef00e05c2ab68832be27772806039` | **PASS** |
| `温室秋茬番茄种植监测数据（2024年8月28日~2025年1月10日）.xlsx` | Autumn Tomato (*Jingcai No. 8*) | 1,428,388 | `194e27a80cf8a19beeb2095264f5f2cc2b286516086e191337d0d878feae4a16` | **PASS** |
| `温室快菜种植监测数据（2024年12月24日~2025年2月6日）.xlsx` | Fast Cabbage (*Jingyan Fast*) | 281,350 | `ebb7e7f6cffbc279dbc668c4b26ff2b916e9fd13b94239288d6323aa325afa14` | **PASS** |

Verification was confirmed via `sha256sum --check metadata/beijing_sha256.txt`.

### 2.2 Worksheet Architecture

Each workbook consists of exactly three worksheets:
1. `生育期` (Growth Stages): Text-based phenological stages and calendar intervals.
2. `空气温湿度` (Air Temperature and Humidity): High-frequency time-series from the Greenhouse Doll II sensor.
3. `土壤墒情` (Soil Moisture and Temperature): Multi-depth time-series from the DZN2 probe.

*Note on Header Offsets:* In the Cucumber workbook, the `土壤墒情` sheet contains an unpopulated top row (`None, None, ...`), requiring `header=1` during programmatic ingestion. In both Tomato workbooks, trailing empty columns (columns 3 and 4) are present in the air sheet and should be dropped.

---

## 3. Sensor Instrumentation & Data Characterization

```
+----------------------------------------------------------------------------------------------------+
|                                    CHINESE SOLAR GREENHOUSE (350 m²)                                |
|                                                                                                    |
|   +--------------------------------------------------------------------------------------------+   |
|   | North Heat-Storage Brick Wall (Height: 2.5 m)                                              |   |
|   +--------------------------------------------------------------------------------------------+   |
|                                                                                                    |
|     Ridge 4 (46.7 m): Soil Cultivation Bed                                                        |
|     Ridge 3 (46.7 m): Soil Cultivation Bed                                                        |
|                                                                                                    |
|     Ridge 2 (46.7 m): [SENSOR CLUSTER AT CENTER]                                                   |
|                        |                                                                           |
|                        +---> "Greenhouse Doll II" (温室娃娃II)                                      |
|                        |     - Air Temperature (°C) [error <= ±0.2 °C]                              |
|                        |     - Air Relative Humidity (%) [error <= ±2 %]                           |
|                        |                                                                           |
|                        +---> "DZN2" Multi-Depth Soil Probe                                         |
|                              - Depth 20 cm: Moisture (%) & Temperature (°C)                        |
|                              - Depth 40 cm: Moisture (%) & Temperature (°C)                        |
|                              - Depth 60 cm: Moisture (%) & Temperature (°C)                        |
|                                                                                                    |
|     Ridge 1 (46.7 m): Soil Cultivation Bed                                                        |
|                                                                                                    |
|   +--------------------------------------------------------------------------------------------+   |
|   | South Transparent Plastic Glazing Film (Ridge Height: 3.7 m)                                |   |
|   +--------------------------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------------------------+
```

### 3.1 Sensor Specifications

1. **Air Environmental Sensor: "Greenhouse Doll II" (温室娃娃II)**
   - Measurement Variables: Air Temperature ($T_{air}$), Air Relative Humidity ($RH_{air}$).
   - Accuracy: Temperature $\le \pm 0.2$ °C; Relative Humidity $\le \pm 2$ %.
   - Nominal Sampling Interval: 5 minutes.
2. **Subsurface Soil Sensor: "DZN2" Multi-Depth Moisture & Temperature Probe**
   - Technology: High-frequency Frequency Domain Reflectometry (FDR) for volumetric moisture; precision thermistors for temperature.
   - Depths: 20 cm, 40 cm, 60 cm.
   - Accuracy: Soil Moisture $\le \pm 3$ %; Soil Temperature $\le \pm 0.5$ °C.
   - Nominal Sampling Interval: Documented as 15 minutes (empirically variable, see Section 4).

### 3.2 Sensor Variable Inventory & Data Dictionary

| Scope | Column Header (Chinese) | Variable Identifier | Measurement Variable | Units | Nominal Rate | Sensor Hardware | Observed Records | Null Cells (NaN) | Clean Range (Min – Max) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| Air | `时间` | `time_air` | Timestamp | ISO 8601 | 5 min | Logger | 95,654 | 0 | 2024-05-01 to 2025-07-03 |
| Air | `空气温度（℃）` | `T_air` | Air Temperature | °C | 5 min | Greenhouse Doll II | 95,654 | 0 | 4.32 to 45.82 °C |
| Air | `空气湿度（%）` | `RH_air` | Air Relative Humidity | % | 5 min | Greenhouse Doll II | 95,654 | 0 | 9.54 to 95.02 % |
| Soil | `时间` | `time_soil` | Timestamp | ISO 8601 | 15 / 5 min | Logger | 55,455 | 0 | 2024-05-01 to 2025-07-03 |
| Soil | `20cm土壤水分（%）` | `SM_20cm` | Soil Moisture (20 cm) | % | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 10.01 to 42.60 % |
| Soil | `40cm土壤水分（%）` | `SM_40cm` | Soil Moisture (40 cm) | % | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 21.39 to 46.60 % |
| Soil | `60cm土壤水分（%）` | `SM_60cm` | Soil Moisture (60 cm) | % | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 26.85 to 46.90 % |
| Soil | `20cm土壤温度（℃）` | `ST_20cm` | Soil Temperature (20 cm) | °C | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 12.30 to 27.70 °C |
| Soil | `40cm土壤温度（℃）` | `ST_40cm` | Soil Temperature (40 cm) | °C | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 10.70 to 27.40 °C |
| Soil | `60cm土壤温度（℃）` | `ST_60cm` | Soil Temperature (60 cm) | °C | 15 / 5 min | DZN2 Probe | 55,455 | 0 | 10.80 to 26.70 °C |

Full machine-readable data dictionary is stored in `metadata/beijing_data_dictionary.csv`.

---

## 4. Empirical Temporal Behavior, Missingness & Anomalies

### 4.1 Record Summary by Experiment

| Crop Experiment | Temporal Coverage | Air Records | Soil Records | Total Records | Documented Records | Agreement |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cucumber (黄瓜)** | 2025-03-06 to 2025-07-03 | 34,322 | 26,128 | **60,450** | 60,450 | **100.0% Exact** |
| **Spring Tomato (春茬番茄)** | 2024-05-01 to 2024-07-10 | 18,791 | 15,464 | **34,255** | 34,256 | **99.997%** |
| **Autumn Tomato (秋茬番茄)** | 2024-08-27 to 2025-01-10 | 38,570 | 9,639 | **48,209** | 48,208 | **99.998%** |
| **Fast Cabbage (快菜)** | 2024-12-25 to 2025-02-06 | 3,971 | 4,224 | **8,195** | 8,196 | **99.988%** |
| **Total** | — | **95,654** | **55,455** | **151,109** | 151,110 | **99.999%** |

The observed row counts match the official ScienceDB deposit description within 1 row per file (differences due to header row handling).

### 4.2 Critical Finding: Unmasked Sentinel Error Values (`-1000.0`)

During DZN2 FDR probe dropouts, the data acquisition unit logged `-1000.0` rather than omitting the record or assigning an IEEE NaN. Crucially, the thermistor channels continued operating normally during these events, demonstrating that FDR circuit communication failed independently of temperature logging.

| File / Crop | Channel | Sentinel `-1000.0` Count | Raw Mean $\pm$ Std | Cleaned Mean $\pm$ Std | Impact Description |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Cucumber** | `40cm土壤水分` | 72 | 41.17 $\pm$ 54.77% | 44.05 $\pm$ 1.90% | Std inflated by 28.8× |
| **Cucumber** | `60cm土壤水分` | 67 | 41.57 $\pm$ 52.82% | 44.25 $\pm$ 0.67% | Std inflated by 78.8× |
| **Cucumber** | `20cm土壤水分` | 1 | 34.63 $\pm$ 6.97% | 34.67 $\pm$ 2.76% | Minimum altered to -1000% |
| **Autumn Tomato** | `20cm, 40cm, 60cm` | 27 each (81 total) | 22.06 $\pm$ 54.40% | 24.93 $\pm$ 4.94% | Pervasive across all 3 depths |
| **Spring Tomato** | All Soil Channels | 0 | 17.83 $\pm$ 3.58% | 17.83 $\pm$ 3.58% | Clean |
| **Fast Cabbage** | All Soil Channels | 0 | 36.19 $\pm$ 3.29% | 36.19 $\pm$ 3.29% | Clean |

> [!CAUTION]
> If these `-1000.0` values are not replaced with `NaN` before standard normalization or regression, gradient calculations and variance calculations will suffer extreme numerical instability.

### 4.3 Diurnal Logging Pattern (Fast Cabbage Air Stream)

Audit of timestamp hours revealed that the Greenhouse Doll II air sensor for fast cabbage was switched off every night:
- **Day records (06:00–20:59):** 3,878 records (97.7%).
- **Night records (21:00–05:59):** Only 93 records (2.3%).
- **Persistent Daily Gaps:** Every day between 16:30/17:30 and 09:30/10:00 the following morning (gaps of 14.5 to 20.5 hours), air readings cease entirely.
- In contrast, the DZN2 soil sensor operated continuously 24 hours a day at 15-minute intervals.

### 4.4 Sampling Frequency Transitions & Continuity

- **Cucumber Soil Transition:** From 2025-03-06 to 2025-04-18 13:00, soil moisture was logged every 15.0 minutes (4,180 records). From 2025-04-18 13:00 through 2025-07-03, logging switched to 5.0-minute intervals (21,948 records).
- **Spring Tomato Soil Interval:** Sampled at 5-minute intervals throughout, with continuous 1–2 second timing jitter (5.016 min, 5.033 min) caused by clock drift.
- **Autumn Tomato Outages:** Longest hardware dropout in the dataset:
  - 17.39-day outage: 2024-11-29 04:45 to 2024-12-16 14:00.
  - 9.51-day outage: 2024-09-29 04:45 to 2024-10-08 17:06.
  - 6.01-day outage: 2024-12-29 10:00 to 2025-01-04 10:15.
- **Cucumber Continuity:** Exceptional continuity. Soil stream has **zero gaps > 1 hour** over 119 days. Air stream has only **two gaps > 1 hour** (1.3 hours on April 30 and 1.2 hours on May 31).

---

## 5. Crop Phenology & Yield-Label Investigation

### 5.1 Phenological Stages Recorded in `生育期`

The `生育期` worksheet in each file records the calendar boundaries of agricultural growth phases:

```
Fast Cabbage (‘京研快菜’)
  |-- 定植 (Transplanting): 2024.12.24
  |-- 苗期 (Seedling): 2024.12.24 - 2025.01.15
  |-- 莲座期 (Rosette): 2025.01.16 - 2025.02.01
  \-- 采收期 (Harvest Period): 2025.02.02 - 2025.02.06

Spring Tomato (‘京采8号’)
  |-- 定植 (Transplanting): 2024.04.01
  |-- 苗期 (Seedling): 2024.04.01 - 2024.04.29
  |-- 开花坐果期 (Flowering & Fruit Setting): 2024.04.30 - 2024.05.11
  |-- 果实膨大期 (Fruit Expansion): 2024.05.12 - 2024.06.04
  |-- 转色期 (Color Turning): 2024.06.05 - 2024.06.11
  \-- 采收期 (Harvest Period): 2024.06.12 - 2024.06.25

Autumn Tomato (‘京采8号’)
  |-- 定植 (Transplanting): 2024.08.27
  |-- 苗期 (Seedling): 2024.08.27 - 2024.09.25
  |-- 开花坐果期 (Flowering & Fruit Setting): 2024.09.26 - 2024.10.05
  |-- 果实膨大期 (Fruit Expansion): 2024.10.06 - 2024.12.22
  |-- 转色期 (Color Turning): 2024.12.23 - 2024.12.26
  \-- 采收期 (Harvest Period): 2024.12.27 - 2025.01.10

Cucumber (‘中农26号’)
  |-- 定植 (Transplanting): 2025.03.06
  |-- 营养生长期 (Vegetative Growth): 2025.03.06 - 2025.03.25
  |-- 开花坐果期 (Flowering & Fruit Setting): 2025.03.26 - 2025.04.07
  \-- 采收期 (Harvest Period): 2025.04.08 - 2025.07.03
```

### 5.2 Verification of Yield / Production Target Availability

A systematic search was conducted across all files, worksheets, headers, text cells, and ScienceDB deposit metadata for harvest mass, fruit counts, cumulative production, or commercial grades.

- **Harvest Mass ($kg$, $kg/m^2$, or $kg/plant$):** ABSENT.
- **Fruit Counts (number of harvested fruits):** ABSENT.
- **Harvest Timestamps (exact harvest dates/times):** ABSENT (only general date range `采收期`).
- **Plant Density / Total Plant Counts:** ABSENT from data tables (greenhouse area is known: 350 m²).
- **Forecasting Target Construction:** **IMPOSSIBLE.** No ground-truth label exists to train or evaluate a yield forecasting model.

> [!IMPORTANT]
> **DECISION RULE VERDICT:**  
> The acceptance criteria require that if yield labels are absent, the dataset must not be used to calculate or report yield forecasting performance.  
> **Status: VERIFIED & ENFORCED.** The Beijing dataset cannot be used as an evaluation benchmark for cucumber yield prediction.

---

## 6. Cross-Dataset Environmental Compatibility Analysis

### 6.1 Structural & Environmental Comparison (Beijing vs. WUR vs. RDA)

| Characteristic | Beijing Greenhouse Dataset | WUR Autonomous Greenhouse 2018 | RDA South Korea Smart Farm |
| :--- | :--- | :--- | :--- |
| **Location** | Beijing, China (39.9°N, 116.4°E) | Bleiswijk, Netherlands (52.0°N, 4.5°E) | Jeonju / Jinju, South Korea |
| **Climate Zone** | Cold semi-arid / Continental monsoon | Temperate maritime (Cfb) | East Asian humid subtropical/continental |
| **Greenhouse Type** | Chinese Solar Greenhouse (brick thermal wall) | Venlo Glasshouse (fully glazed) | Venlo or Plastic Multi-span greenhouse |
| **Cultivation Substrate** | Soil ridge planting (4 ridges, East-West) | Rockwool slabs (closed-loop hydroponic) | Rockwool or coir hydroponic gutters |
| **Heating / Climate Control** | Passive solar heat storage + night insulation quilt | Active hot water pipe circuits (rail + grow) | Active hot water pipes / heat pumps |
| **Lighting** | Natural sunlight | High-pressure sodium (HPS) / Assimilation LED | Natural sunlight + supplemental LED |
| **Cucumber Cultivar** | ‘中农26号’ (Zhongnong No. 26) | ‘Hi Power’ | ‘Baekdadagi’ / ‘Nakhap’ |
| **Sensor Variables** | $T_{air}$, $RH_{air}$, Soil Moisture (3 depths), Soil Temp (3 depths) | $T_{air}$, $RH_{air}$, $CO_{2}$, $HumDef$, Pipe Temps, Actuators, Weather | $T_{air}$, $RH_{air}$, $CO_{2}$, Radiation, Irrigation, Drain |
| **Temporal Frequency** | 5-minute air, 5/15-minute soil | 5-minute climate, daily harvest | 1-minute / 5-minute climate, daily/weekly harvest |
| **Yield Labels** | **None** | Complete daily cumulative ($kg/m^2$) | Complete harvest records ($kg$) |

### 6.2 Variable Harmonization & Environmental Feature Overlap

```
+-----------------------------------+               +-----------------------------------+
|     BEIJING GREENHOUSE SENSOR     |               |      WUR 2018 GREENHOUSE DATA     |
+-----------------------------------+               +-----------------------------------+
|  时间 (Timestamp)                 | <===========> |  GHtime (Normalized Timestamp)    |
|  空气温度（℃） [T_air]            | <===========> |  Tair (°C)                        |
|  空气湿度（%） [RH_air]           | <===========> |  RHair (%)                        |
|  *Derived VPD (kPa) / HumDef*     | <===========> |  HumDef (g/m³)                    |
+-----------------------------------+               +-----------------------------------+
|  20cm/40cm/60cm 土壤水分 (%)      |      [--]     |  (Hydroponic Rockwool Slab EC)    |
|  20cm/40cm/60cm 土壤温度 (℃)      |      [--]     |  (PipeLow / PipeGrow Circuit °C)  |
+-----------------------------------+               +-----------------------------------+
|  [NO YIELD LABELS]                |      [X]      |  Total_Prod_cum (kg/m²)           |
+-----------------------------------+               +-----------------------------------+
```

- **Direct Environmental Alignment:**
  $T_{air}$ and $RH_{air}$ are recorded at identical 5-minute frequencies across both datasets.
  From $T_{air}$ and $RH_{air}$, the Vapor Pressure Deficit ($VPD$) or absolute humidity deficit ($HumDef$) can be calculated analytically using the Tetens equation:
  $$e_s(T) = 0.61078 \exp\left(\frac{17.27 \cdot T}{T + 237.3}\right) \quad [\text{kPa}]$$
  $$VPD = e_s(T_{air}) \cdot \left(1 - \frac{RH_{air}}{100}\right) \quad [\text{kPa}]$$
  $$HumDef = \frac{216.7 \cdot VPD}{T_{air} + 273.15} \quad [\text{g/m}^3]$$
- **Microclimate Distribution Shift:**
  - Beijing cucumber season (March–July) experiences severe high-temperature excursions (maximum $43.26$ °C, 95th percentile $36.28$ °C) and low relative humidity (minimum $9.54$ %, mean $64.44$ %).
  - WUR cucumber season (August–December) is actively climate-controlled within a much narrower band (typically 18.0–26.0 °C, humidity buffered at 70–85% with high assimilation lighting and pipe heating).
  - This contrast provides an ideal testbed for **evaluating whether representation models trained on stable Dutch greenhouses collapse when exposed to continental summer heat spikes.**

---

## 7. Recommended Downstream Research Applications

While the absence of yield labels rules out direct yield forecasting, the dataset possesses unique structural properties that make it highly valuable for three specific research tracks:

### Application 1: Self-Supervised Sensor Representation Pretraining

- **Data Volume:** 60,450 cucumber time-steps + 90,659 additional vegetable time-steps at 5-minute resolution.
- **Pretraining Task:** Masked autoencoding or autoregressive sequence modeling on multivariate sensor channels:
  $$\mathbf{x}_t = [T_{air}, RH_{air}, SM_{20}, SM_{40}, SM_{60}, ST_{20}, ST_{40}, ST_{60}]^T$$
- **Pretext Objectives:**
  1. *Temporal Masking:* Mask random 2-hour to 24-hour windows and reconstruct missing environmental trajectories.
  2. *Cross-Modal Reconstruction:* Predict subsurface soil temperature and moisture from air climate inputs, forcing the encoder to learn thermal conduction and evapotranspiration dynamics.
- **Transfer Target:** Transfer frozen or fine-tuned representations to downstream yield prediction models operating on WUR or RDA data.

### Application 2: Cross-Dataset Environmental Distribution-Shift Benchmark

- **Scientific Question:** How well do learned environmental representations generalize across fundamentally different agricultural engineering paradigms (solar greenhouse vs. Venlo glasshouse)?
- **Evaluation Protocol:**
  1. Train sequence encoders on Dutch greenhouse climate dynamics (WUR).
  2. Evaluate out-of-distribution perplexity, representation collapse, and feature drift on Beijing cucumber climate sequences.
  3. Benchmark domain-adaptation techniques (e.g. coral loss, adversarial domain alignment) on the Beijing feature space.

### Application 3: Real-World Sensor Dropout & Robustness Benchmark

The empirical failure modes identified in this audit provide exact parameters for designing synthetic dropout experiments:
- **Diurnal Power Outage:** Drop sensor streams during nighttime hours ($17:00$ to $09:30$) following the Fast Cabbage empirical pattern.
- **Hardware Blackout:** Introduce 6-day to 17-day continuous missing intervals following the Autumn Tomato outage profile.
- **FDR Channel Failure:** Inject unmasked sentinel codes (`-1000.0`) at single sensor depths while leaving companion channels intact, testing whether imputation models detect physical inconsistency.
- **Multi-Rate Irregular Sampling:** Test inference pipelines on dynamic sampling transitions (15-minute to 5-minute shifts).

---

## 8. Data Ingestion & Preprocessing Specification

Any downstream model consuming the Beijing dataset must incorporate the following preprocessing steps:

1. **Header Normalization:**
   - Cucumber soil sheet must be read with `header=1` (row index 1 in openpyxl / pandas).
   - Tomato air sheets must drop trailing unpopulated columns (`df.dropna(axis=1, how='all')`).
2. **Sentinel Error Code Masking:**
   - Values equal to `-1000.0` in all soil moisture columns must be replaced with `np.nan` prior to computing scaling parameters.
3. **Temporal Alignment & Resampling:**
   - Air (5-min) and soil (15-min or 5-min) streams must be reindexed to a continuous 5-minute or 15-minute datetime grid using right-closed forward interpolation or linear interpolation for gaps $< 30$ minutes.
4. **Leakage & Partitioning Isolation:**
   - If pretraining representations on this dataset, no test splits from WUR or RDA may be consulted. The Beijing dataset represents a strictly independent external domain.

---

## 9. Conclusion & Acceptance Sign-Off

- **Provenance & Documentation:** Complete. DOI, institution, coordinates, greenhouse structure, and sensor models verified.
- **Integrity:** Complete. Checksums verified across all 4 raw files.
- **Cucumber Records:** Complete. 60,450 records isolated (March 6 – July 3, 2025).
- **Missingness & Outages:** Quantified. Nighttime logging in Fast Cabbage and multi-day outages in Autumn Tomato documented.
- **Sensor Calibration & Sentinels:** Quantified. `-1000.0` FDR dropouts characterized.
- **Yield Label Availability:** Verified ABSENT. Decision Rule strictly enforced.
- **Deliverables Produced:**
  - `docs/dataset_audits/beijing_sensor_audit.md` (this report)
  - `metadata/beijing_data_dictionary.csv`
  - `metadata/beijing_metadata.json`
  - `metadata/beijing_sha256.txt`
  - `reports/data_audit/beijing_inventory.txt`
  - `reports/data_audit/beijing_file_tree.txt`
  - `reports/data_audit/beijing_quality_report.txt`
  - `reports/data_audit/beijing_value_inspection.txt`
  - `scripts/data_audit/beijing_quality_audit.py`
  - `scripts/data_audit/beijing_value_inspection.py`
  - `scripts/data_audit/build_beijing_data_dictionary.py`

**Audit Status:** **ACCEPTED & COMPLETE.**

# Common Data Schema

> Generated automatically by `scripts/data_processing/build_common_schema.py`

## Objective

Provide a single, consistent data representation for all greenhouse datasets in
POLAR-Cuke, while **preserving original source identities**, temporal information,
and provenance — and preventing target leakage.

---

## Datasets Covered

| `dataset_id`    | Description                                       | Timezone (original) | Period            |
|-----------------|---------------------------------------------------|---------------------|-------------------|
| `wur_2018`      | WUR Autonomous Greenhouse Challenge 2018          | CET (UTC+1)         | Aug–Dec 2018      |
| `rda_2024`      | RDA Smart Farm Korea 2024 (cucumber subset)       | KST (UTC+9)         | Jan–Dec 2024      |
| `beijing_2025`  | Beijing Xiaotangshan Greenhouse 2025              | CST (UTC+8)         | Mar–Jul 2025      |

All stored timestamps are **UTC** (`YYYY-MM-DDTHH:MM:SSZ`).

---

## Mandatory Metadata Fields

| Field            | Type    | Description                                                               |
|------------------|---------|---------------------------------------------------------------------------|
| `sample_id`      | string  | Globally unique row identifier: `{dataset_id}:{compartment_id}:{timestamp}` |
| `dataset_id`     | string  | Dataset identifier (see table above)                                      |
| `farm_id`        | string  | Farm/site identifier (e.g. `wur_bleiswijk`, `rda_farm_01`)               |
| `compartment_id` | string  | Greenhouse compartment or section                                          |
| `crop_id`        | string  | Standardized crop name (always `cucumber` for POLAR-Cuke)                |
| `season_id`      | string  | Growing season identifier (e.g. `2018_autumn`, `2024_season_1`)           |
| `timestamp`      | string  | ISO-8601 UTC observation time (`YYYY-MM-DDTHH:MM:SSZ`)                   |
| `available_at`   | string  | ISO-8601 UTC time when this record is first available without leakage    |
| `source_id`      | string  | Relative path to the originating raw file                                 |
| `missing_mask`   | string  | JSON boolean dict: `{"column": true_if_NaN, ...}`                        |

---

## Leakage Prevention (`available_at`)

The `available_at` timestamp marks the **earliest wall-clock time** at which a
record may be used as a feature or target without causing data leakage.

| Record type        | `available_at` rule                                                       |
|--------------------|---------------------------------------------------------------------------|
| Environment sensor | Same as `timestamp` (real-time telemetry)                                |
| Growth observation | End of observation day (`23:59:59 UTC`) — observed manually              |
| Harvest/production | End of harvest day (`23:59:59 UTC`) — recorded after weighing/shipment   |

> **Critical:** Daily cumulative harvest (`Total_Prod_cum` in WUR) must **not** be
> used as an input feature for any intra-day (5-minute) prediction step.
> Always filter `available_at ≤ prediction_time` when constructing training sets.

---

## Identifier Conventions

### `farm_id`

| Dataset   | Pattern                 | Example               |
|-----------|-------------------------|-----------------------|
| WUR       | `wur_bleiswijk`         | `wur_bleiswijk`       |
| RDA       | `rda_farm_<NN>`         | `rda_farm_01`         |
| Beijing   | `beijing_xiaotangshan`  | `beijing_xiaotangshan`|

### `compartment_id`

| Dataset   | Pattern                       | Example             |
|-----------|-------------------------------|---------------------|
| WUR       | `{TeamName}:{record_type}`    | `AiCU:climate`      |
| RDA       | `rda_farm_<NN>_comp`          | `rda_farm_01_comp`  |
| Beijing   | `bj_greenhouse_1`             | `bj_greenhouse_1`   |

### `season_id`

| Dataset   | Pattern               | Example           |
|-----------|-----------------------|-------------------|
| WUR       | `2018_autumn`         | `2018_autumn`     |
| RDA       | `2024_season_{작기}`  | `2024_season_1`   |
| Beijing   | `2025_spring`         | `2025_spring`     |

---

## Timezone Normalization

All timestamps are stored in **UTC** (`Z` suffix).

| Dataset   | Original timezone | UTC offset applied |
|-----------|--------------------|--------------------|
| WUR       | CET (UTC+1)        | −1 h               |
| RDA       | KST (UTC+9)        | −9 h               |
| Beijing   | CST (UTC+8)        | −8 h               |

---

## Common Variable Namespace

| Common name               | Unit   | Source datasets         | Description                         |
|---------------------------|--------|-------------------------|-------------------------------------|
| `indoor_temp_c`           | °C     | wur_2018, rda_2024, beijing_2025 | Indoor air temperature       |
| `indoor_rh_pct`           | %      | wur_2018, rda_2024, beijing_2025 | Indoor relative humidity     |
| `indoor_co2_ppm`          | ppm    | wur_2018, rda_2024      | Indoor CO₂ concentration            |
| `outdoor_temp_c`          | °C     | rda_2024                | Outdoor air temperature             |
| `solar_irradiance_wm2`    | W/m²   | rda_2024                | Global solar irradiance             |
| `wind_speed_ms`           | m/s    | rda_2024                | Wind speed                          |
| `soil_temp_c`             | °C     | rda_2024                | Soil temperature                    |
| `soil_moisture_20cm_pct`  | %      | beijing_2025            | Soil volumetric moisture at 20 cm   |
| `prod_total_cum_kgm2`     | kg/m²  | wur_2018                | Cumulative total production         |
| `shipment_qty_g`          | g      | rda_2024                | Daily shipment quantity             |
| `plant_height_cm`         | cm     | rda_2024                | Stem length from soil to tip        |

---

## Interim Data Layout

```
data/
  interim/
    wur/
      AiCU_climate.parquet
      AiCU_production.parquet
      AiCU_irrigation.parquet
      Croperators_climate.parquet
      ...  (6 teams × 3 file types)
    rda/
      rda_cucumber_environment.parquet
      rda_cucumber_growth.parquet
      rda_cucumber_production.parquet
    beijing/
      beijing_cucumber.parquet
```

All Parquet files use **Snappy compression** and preserve the schema columns
listed above plus dataset-specific feature columns.

---

## Manifests & Dictionaries

| File                                            | Description                                           |
|-------------------------------------------------|-------------------------------------------------------|
| `metadata/data_manifest.csv`                    | One row per sample, all schema metadata fields        |
| `data_manifest.csv`                             | Top-level copy of the manifest                        |
| `metadata/data_dictionary.xlsx`                 | Variable definitions: original → common name + units |
| `data_dictionary.xlsx`                          | Top-level copy of the dictionary                      |
| `reports/common_schema_missingness_report.txt`  | Per-file missing-value statistics                     |

---

## Raw Data Integrity

Raw files are **never modified**. SHA-256 checksums are stored in:

- `metadata/wur_sha256.txt`
- `metadata/rda_sha256.txt`
- `metadata/beijing_sha256.txt`

Verify with:
```bash
sha256sum --check metadata/wur_sha256.txt
sha256sum --check metadata/rda_sha256.txt
sha256sum --check metadata/beijing_sha256.txt
```

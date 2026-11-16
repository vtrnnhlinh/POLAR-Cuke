#!/usr/bin/env python3
"""
build_common_schema.py
======================
Issue #4 — Define common data schema and generate dataset manifests.

Reads raw data for three datasets:
  - WUR Autonomous Greenhouse Challenge 2018  (data/raw/wur/)
  - RDA Smart Farm Korea 2024                 (data/raw/rda/)
  - Beijing Greenhouse 2024-25                (data/raw/beijing/)

Outputs:
  - data/interim/wur/     — Parquet files per WUR compartment
  - data/interim/rda/     — Parquet files for RDA cucumber data
  - data/interim/beijing/ — Parquet files for Beijing cucumber data
  - metadata/data_manifest.csv
  - metadata/data_dictionary.xlsx
  - reports/common_schema_missingness_report.txt
  - docs/common_data_schema.md
"""

import os
import re
import json
import shutil
import warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
RAW_WUR = ROOT / "data" / "raw" / "wur"
RAW_RDA = ROOT / "data" / "raw" / "rda" / "2024"
RAW_BJ  = ROOT / "data" / "raw" / "beijing"
INTERIM = ROOT / "data" / "interim"
META_DIR = ROOT / "metadata"
REPORTS_DIR = ROOT / "reports"
DOCS_DIR = ROOT / "docs"

for d in [INTERIM/"wur", INTERIM/"rda", INTERIM/"beijing",
          META_DIR, REPORTS_DIR, DOCS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Common schema fields (in order) ──────────────────────────────────────────
SCHEMA_COLS = [
    "sample_id",
    "dataset_id",
    "farm_id",
    "compartment_id",
    "crop_id",
    "season_id",
    "timestamp",
    "available_at",
    "source_id",
    "missing_mask",
]

manifest_rows = []
dict_rows     = []
report_lines  = [
    "Common Schema Missingness Report",
    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "=" * 72,
    "",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def excel_serial_to_dt(serial: float) -> datetime:
    """Excel serial → Python datetime (origin 1899-12-30)."""
    return datetime(1899, 12, 30) + timedelta(days=float(serial))


def make_sample_id(dataset_id: str, compartment_id: str, timestamp: str) -> str:
    return f"{dataset_id}:{compartment_id}:{timestamp}"


def missing_mask_df(df: pd.DataFrame, feature_cols: list) -> pd.Series:
    """Vectorised missing_mask: JSON bool dict of which cols are NaN."""
    present = [c for c in feature_cols if c in df.columns]
    return df[present].isna().apply(lambda r: json.dumps(r.to_dict()), axis=1)


def to_numeric_all(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Cast listed columns to float, coercing errors to NaN."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def save_parquet(df: pd.DataFrame, path: Path, label: str):
    """Write DataFrame to Snappy-compressed Parquet; also add to report."""
    # Cast any object columns that look numeric
    for c in df.columns:
        if df[c].dtype == object and c not in SCHEMA_COLS:
            df[c] = pd.to_numeric(df[c], errors="ignore")

    pq.write_table(pa.Table.from_pandas(df, preserve_index=False),
                   path, compression="snappy")
    print(f"  Wrote {len(df):,} rows → {label}")

    # Missingness for report
    report_lines.append(f"File: {path.relative_to(ROOT)}")
    report_lines.append(f"  Rows: {len(df):,}  Columns: {len(df.columns)}")
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        report_lines.append("  → No missing values.")
    else:
        for col, cnt in missing.items():
            pct = 100 * cnt / len(df)
            report_lines.append(f"  {col:<50} {cnt:>8,}  ({pct:5.1f}%)")
    report_lines.append("")


# ─── 1. WUR 2018 ──────────────────────────────────────────────────────────────
print("=" * 60)
print("Processing WUR 2018 …")

WUR_COMPARTMENTS = [
    "AiCU", "Croperators", "DeepGreens", "iGrow",
    "Reference(Growers)", "Sonoma"
]

# Actual WUR column names (comma-delimited CSVs, no Excel serial header)
WUR_CLIMATE_MAP = {
    "CO2air":   ("indoor_co2_ppm",          "ppm",   "5min", "Indoor CO₂ concentration"),
    "HumDef":   ("indoor_hum_deficit_gpkg", "g/kg",  "5min", "Indoor humidity deficit"),
    "PipeGrow": ("pipe_grow_temp_c",        "°C",    "5min", "Grow pipe temperature"),
    "PipeLow":  ("pipe_low_temp_c",         "°C",    "5min", "Low pipe temperature"),
    "RHair":    ("indoor_rh_pct",           "%",     "5min", "Indoor relative humidity"),
    "Tair":     ("indoor_temp_c",           "°C",    "5min", "Indoor air temperature"),
    "AssimLight":("assimilation_light_wm2", "W/m²",  "5min", "Assimilation lamp intensity"),
    "BlackScr": ("blackout_screen_pct",     "%",     "5min", "Black screen closure"),
    "EnScr":    ("energy_screen_pct",       "%",     "5min", "Energy screen closure"),
    "VentLee":  ("vent_lee_pct",            "%",     "5min", "Leeward vent opening"),
    "Ventwind": ("vent_wind_pct",           "%",     "5min", "Windward vent opening"),
}

WUR_PROD_MAP = {
    "ProdA_cum":      ("prod_a_cum_kgm2",    "kg/m²", "daily", "Cumulative production section A"),
    "ProdB_cum":      ("prod_b_cum_kgm2",    "kg/m²", "daily", "Cumulative production section B"),
    "Total_Prod_cum": ("prod_total_cum_kgm2","kg/m²", "daily", "Total cumulative production"),
    "ProdA_num":      ("prod_a_num_fruits",  "count", "daily", "Harvested fruit count section A"),
    "ProdB_num":      ("prod_b_num_fruits",  "count", "daily", "Harvested fruit count section B"),
    "Prod_value_cum": ("prod_value_cum_eur", "EUR",   "daily", "Cumulative production value"),
}

WUR_IRR_MAP = {
    "EC_Drain": ("ec_drain_mscm",  "mS/cm", "5min", "Drain EC"),
    "drain":    ("drain_ml_m2",    "mL/m²", "5min", "Drain volume"),
    "pH_Drain": ("ph_drain",       "-",     "5min", "Drain pH"),
    "water":    ("water_ml_m2",    "mL/m²", "5min", "Water supply"),
}

WUR_SEASON = "2018_autumn"
WUR_FARM   = "wur_bleiswijk"
WUR_DS     = "wur_2018"
WUR_CROP   = "cucumber"
# WUR trial: September–December 2018 (Bleiswijk, NL)  UTC = local CET − 1h
WUR_TZ_OFFSET = timedelta(hours=1)   # CET offset to subtract → UTC


def parse_wur_ts(val) -> datetime | None:
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return excel_serial_to_dt(f)
    except (ValueError, TypeError):
        return None


def process_wur_file(comp: str, file_name: str, col_map: dict,
                     record_type: str, is_harvest: bool):
    path = RAW_WUR / comp / file_name
    if not path.exists():
        print(f"    [skip] {path.name} not found")
        return

    df = pd.read_csv(path, sep=",", decimal=".")
    # Timestamp column is named 'GHtime' or 'time'
    ts_col = next((c for c in df.columns if c.lower() in {"ghtime", "time"}), None)
    if ts_col is None:
        print(f"    [skip] no timestamp col in {path.name}")
        return

    df["_dt"] = df[ts_col].apply(parse_wur_ts)
    df = df.dropna(subset=["_dt"])

    # Convert CET → UTC
    df["timestamp"] = df["_dt"].apply(
        lambda d: (d - WUR_TZ_OFFSET).strftime("%Y-%m-%dT%H:%M:%SZ"))

    if is_harvest:
        # Harvest day is recorded; available only at end of day
        df["available_at"] = df["_dt"].apply(
            lambda d: (d - WUR_TZ_OFFSET).replace(
                hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        df["available_at"] = df["timestamp"]

    # Rename feature columns
    rename_map = {orig: v[0] for orig, v in col_map.items() if orig in df.columns}
    df = df.rename(columns=rename_map)
    feat_cols = [v[0] for orig, v in col_map.items() if orig in rename_map]
    df = to_numeric_all(df, feat_cols)

    compartment_id = comp
    df["dataset_id"]     = WUR_DS
    df["farm_id"]        = WUR_FARM
    df["compartment_id"] = compartment_id
    df["crop_id"]        = WUR_CROP
    df["season_id"]      = WUR_SEASON
    df["source_id"]      = f"data/raw/wur/{comp}/{file_name}"
    df["missing_mask"]   = missing_mask_df(df, feat_cols)
    df["sample_id"]      = df.apply(
        lambda r: make_sample_id(WUR_DS, f"{compartment_id}:{record_type}", r["timestamp"]),
        axis=1)

    out_cols = [c for c in SCHEMA_COLS + feat_cols if c in df.columns]
    df_out = df[out_cols].copy().reset_index(drop=True)

    slug = comp.replace("(", "").replace(")", "").replace(" ", "_")
    out_path = INTERIM / "wur" / f"{slug}_{record_type}.parquet"
    save_parquet(df_out, out_path, f"wur/{slug}_{record_type}.parquet")

    for _, r in df_out.iterrows():
        manifest_rows.append({
            "sample_id":        r["sample_id"],
            "dataset_id":       WUR_DS,
            "farm_id":          WUR_FARM,
            "compartment_id":   compartment_id,
            "crop_id":          WUR_CROP,
            "season_id":        WUR_SEASON,
            "timestamp":        r["timestamp"],
            "available_at":     r["available_at"],
            "source_file":      f"data/raw/wur/{comp}/{file_name}",
            "is_harvest_event": is_harvest,
            "record_type":      record_type,
        })

    for orig, (common, unit, freq, desc) in col_map.items():
        if orig in rename_map:
            dict_rows.append({
                "dataset_id":    WUR_DS,
                "source_file":   f"data/raw/wur/{comp}/{file_name}",
                "original_name": orig,
                "common_name":   common,
                "unit":          unit,
                "dtype":         "float64",
                "sampling_freq": freq,
                "description":   desc,
            })


for comp in WUR_COMPARTMENTS:
    print(f"  [{comp}]")
    process_wur_file(comp, "Greenhouse_climate.csv", WUR_CLIMATE_MAP, "climate",   False)
    process_wur_file(comp, "Production.csv",         WUR_PROD_MAP,    "production", True)
    process_wur_file(comp, "Irrigation.csv",         WUR_IRR_MAP,     "irrigation", False)

print(f"WUR done. Manifest rows so far: {len(manifest_rows):,}")

# ─── 2. RDA Smart Farm 2024 ───────────────────────────────────────────────────
print("=" * 60)
print("Processing RDA 2024 (cucumber only) …")

RDA_DS    = "rda_2024"
RDA_CROP  = "cucumber"
RDA_TZ    = timedelta(hours=9)   # KST → UTC

# Load cultivation metadata for farm ID/season mapping
cult_df   = pd.read_excel(RAW_RDA / "재배정보_2024" / "재배정보_2024.xlsx")
cuke_cult = cult_df[cult_df["품목"] == "오이"].copy()

farm_no_to_id = {
    int(row["농가명"]): f"rda_farm_{int(row['농가명']):02d}"
    for _, row in cuke_cult.iterrows()
}
# (농가명, 작기) → season_id
season_map = {
    (int(row["농가명"]), int(row["작기"])): f"2024_season_{int(row['작기'])}"
    for _, row in cuke_cult.iterrows()
}


def rda_farm_id(no):
    n = int(no)
    return farm_no_to_id.get(n, f"rda_farm_{n:02d}")


def rda_season(no, cycle):
    return season_map.get((int(no), int(cycle)), f"2024_season_{int(cycle)}")


def parse_rda_ts_kst(s) -> datetime | None:
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"]:
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    return None


# ── 2a. Environment ────────────────────────────────────────────────────────────
print("  Reading RDA environment file (cucumber rows only) …")

RDA_ENV_COLS = {
    "온도_외부":       ("outdoor_temp_c",       "°C",   "hourly", "Outdoor air temperature"),
    "풍향_외부":       ("wind_direction_deg",   "°",    "hourly", "Wind direction outside"),
    "풍속_외부":       ("wind_speed_ms",        "m/s",  "hourly", "Wind speed outside"),
    "일사량_외부":     ("solar_irradiance_wm2", "W/m²", "hourly", "Solar irradiance outside"),
    "누적일사량_외부": ("solar_irr_cum_wm2",    "W/m²", "hourly", "Cumulative solar irradiance"),
    "강우감지":        ("rain_detected",        "0/1",  "hourly", "Rain detection binary"),
    "온도_내부":       ("indoor_temp_c",        "°C",   "hourly", "Indoor air temperature"),
    "상대습도_내부":   ("indoor_rh_pct",        "%",    "hourly", "Indoor relative humidity"),
    "잔존 CO2":       ("indoor_co2_ppm",        "ppm",  "hourly", "Indoor CO₂ concentration"),
    "토양온도":        ("soil_temp_c",          "°C",   "hourly", "Soil temperature"),
}

env_file = RAW_RDA / "환경_2024" / "환경_2024(가지,국화,수박,오이,참외).csv"
cuke_env_chunks = []
for chunk in pd.read_csv(env_file, encoding="cp949", chunksize=50_000):
    c = chunk[chunk["품목"] == "오이"].copy()
    if not c.empty:
        cuke_env_chunks.append(c)

rda_env = pd.concat(cuke_env_chunks, ignore_index=True)
print(f"  Loaded {len(rda_env):,} env rows")

rda_env["_dt_kst"] = rda_env["측정시간"].apply(parse_rda_ts_kst)
rda_env = rda_env.dropna(subset=["_dt_kst"])
rda_env["timestamp"]   = rda_env["_dt_kst"].apply(lambda d: (d - RDA_TZ).strftime("%Y-%m-%dT%H:%M:%SZ"))
rda_env["available_at"] = rda_env["timestamp"]

feat_rename = {orig: v[0] for orig, v in RDA_ENV_COLS.items() if orig in rda_env.columns}
rda_env = rda_env.rename(columns=feat_rename)
env_feat_cols = [v[0] for orig, v in RDA_ENV_COLS.items() if orig in feat_rename]
rda_env = to_numeric_all(rda_env, env_feat_cols)

rda_env["farm_id"]       = rda_env["농가명"].apply(rda_farm_id)
rda_env["compartment_id"] = rda_env["농가명"].apply(lambda x: f"{rda_farm_id(x)}_comp")
rda_env["season_id"]     = rda_env.apply(lambda r: rda_season(r["농가명"], r["작기"]), axis=1)
rda_env["dataset_id"]    = RDA_DS
rda_env["crop_id"]       = RDA_CROP
rda_env["source_id"]     = "data/raw/rda/2024/환경_2024/환경_2024(가지,국화,수박,오이,참외).csv"
rda_env["missing_mask"]  = missing_mask_df(rda_env, env_feat_cols)
rda_env["sample_id"]     = rda_env.apply(
    lambda r: make_sample_id(RDA_DS, r["compartment_id"], r["timestamp"]), axis=1)

out_cols = [c for c in SCHEMA_COLS + env_feat_cols if c in rda_env.columns]
df_rda_env = rda_env[out_cols].reset_index(drop=True)
save_parquet(df_rda_env, INTERIM/"rda"/"rda_cucumber_environment.parquet",
             "rda/rda_cucumber_environment.parquet")

for _, r in df_rda_env.iterrows():
    manifest_rows.append({
        "sample_id":        r["sample_id"],
        "dataset_id":       RDA_DS,
        "farm_id":          r["farm_id"],
        "compartment_id":   r["compartment_id"],
        "crop_id":          RDA_CROP,
        "season_id":        r["season_id"],
        "timestamp":        r["timestamp"],
        "available_at":     r["available_at"],
        "source_file":      "data/raw/rda/2024/환경_2024/환경_2024(가지,국화,수박,오이,참외).csv",
        "is_harvest_event": False,
        "record_type":      "environment",
    })

for orig, (common, unit, freq, desc) in RDA_ENV_COLS.items():
    if orig in feat_rename:
        dict_rows.append({
            "dataset_id":    RDA_DS,
            "source_file":   "data/raw/rda/2024/환경_2024/...",
            "original_name": orig,
            "common_name":   common,
            "unit":          unit,
            "dtype":         "float64",
            "sampling_freq": freq,
            "description":   desc,
        })

# ── 2b. Growth ─────────────────────────────────────────────────────────────────
print("  Reading RDA growth file …")

RDA_GROWTH_COLS = {
    "초장":           ("plant_height_cm",   "cm",  "weekly", "Stem length from soil to tip"),
    "마디번호":        ("node_number",       "int", "weekly", "Node number at measurement"),
    "줄기굵기":        ("stem_diam_mm",      "mm",  "weekly", "Stem diameter"),
    "절간장":          ("internode_len_cm",  "cm",  "weekly", "Internode length"),
    "엽장":            ("leaf_length_cm",    "cm",  "weekly", "Leaf length"),
    "엽폭":            ("leaf_width_cm",     "cm",  "weekly", "Leaf width"),
    "엽수":            ("leaf_count",        "int", "weekly", "Number of leaves"),
    "마디별 암꽃유무": ("node_female_flower", "0/1","weekly", "Female flower present at node"),
    "마디별 착과수":   ("node_fruit_count",  "int", "weekly", "Fruit count at node"),
}

growth_file = RAW_RDA / "생육_2024" / "생육_오이_2024.csv"
rda_growth  = pd.read_csv(growth_file, encoding="cp949")
rda_growth["_dt"] = pd.to_datetime(rda_growth["조사일자"], errors="coerce")
rda_growth = rda_growth.dropna(subset=["_dt"])
rda_growth["timestamp"]   = rda_growth["_dt"].apply(lambda d: (d - RDA_TZ).strftime("%Y-%m-%dT%H:%M:%SZ"))
rda_growth["available_at"] = rda_growth["_dt"].apply(
    lambda d: (d - RDA_TZ).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ"))

feat_rename_g = {orig: v[0] for orig, v in RDA_GROWTH_COLS.items() if orig in rda_growth.columns}
rda_growth = rda_growth.rename(columns=feat_rename_g)
growth_feat_cols = [v[0] for orig, v in RDA_GROWTH_COLS.items() if orig in feat_rename_g]
rda_growth = to_numeric_all(rda_growth, growth_feat_cols)

rda_growth["farm_id"]       = rda_growth["농가명"].apply(rda_farm_id)
rda_growth["compartment_id"] = rda_growth["농가명"].apply(lambda x: f"{rda_farm_id(x)}_comp")
rda_growth["season_id"]     = rda_growth.apply(lambda r: rda_season(r["농가명"], r["작기"]), axis=1)
rda_growth["dataset_id"]    = RDA_DS
rda_growth["crop_id"]       = RDA_CROP
rda_growth["source_id"]     = "data/raw/rda/2024/생육_2024/생육_오이_2024.csv"
rda_growth["missing_mask"]  = missing_mask_df(rda_growth, growth_feat_cols)
rda_growth["sample_id"]     = rda_growth.apply(
    lambda r: make_sample_id(RDA_DS, f"{r['compartment_id']}:growth", r["timestamp"]), axis=1)

out_cols = [c for c in SCHEMA_COLS + growth_feat_cols if c in rda_growth.columns]
df_rda_growth = rda_growth[out_cols].reset_index(drop=True)
save_parquet(df_rda_growth, INTERIM/"rda"/"rda_cucumber_growth.parquet",
             "rda/rda_cucumber_growth.parquet")

for _, r in df_rda_growth.iterrows():
    manifest_rows.append({
        "sample_id":        r["sample_id"],
        "dataset_id":       RDA_DS,
        "farm_id":          r["farm_id"],
        "compartment_id":   r["compartment_id"],
        "crop_id":          RDA_CROP,
        "season_id":        r["season_id"],
        "timestamp":        r["timestamp"],
        "available_at":     r["available_at"],
        "source_file":      "data/raw/rda/2024/생육_2024/생육_오이_2024.csv",
        "is_harvest_event": False,
        "record_type":      "growth",
    })

for orig, (common, unit, freq, desc) in RDA_GROWTH_COLS.items():
    if orig in feat_rename_g:
        dict_rows.append({
            "dataset_id":    RDA_DS,
            "source_file":   "data/raw/rda/2024/생육_2024/생육_오이_2024.csv",
            "original_name": orig,
            "common_name":   common,
            "unit":          unit,
            "dtype":         "float64",
            "sampling_freq": freq,
            "description":   desc,
        })

# ── 2c. Production ─────────────────────────────────────────────────────────────
print("  Reading RDA production file …")

prod_file = RAW_RDA / "생산_2024" / "생산_2024.csv"
rda_prod  = pd.read_csv(prod_file, encoding="cp949")
cuke_prod = rda_prod[rda_prod["품목"] == "오이"].copy()
cuke_prod["_dt"] = pd.to_datetime(cuke_prod["출하일자"], errors="coerce")
cuke_prod = cuke_prod.dropna(subset=["_dt"])
cuke_prod["timestamp"]   = cuke_prod["_dt"].apply(lambda d: (d - RDA_TZ).strftime("%Y-%m-%dT%H:%M:%SZ"))
cuke_prod["available_at"] = cuke_prod["_dt"].apply(
    lambda d: (d - RDA_TZ).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ"))

cuke_prod = cuke_prod.rename(columns={"총출하량": "shipment_qty_g", "판매금액": "sales_krw"})
prod_feat_cols = ["shipment_qty_g", "sales_krw"]
cuke_prod = to_numeric_all(cuke_prod, prod_feat_cols)

cuke_prod["farm_id"]       = cuke_prod["농가명"].apply(rda_farm_id)
cuke_prod["compartment_id"] = cuke_prod["농가명"].apply(lambda x: f"{rda_farm_id(x)}_comp")
cuke_prod["season_id"]     = cuke_prod.apply(lambda r: rda_season(r["농가명"], r["작기"]), axis=1)
cuke_prod["dataset_id"]    = RDA_DS
cuke_prod["crop_id"]       = RDA_CROP
cuke_prod["source_id"]     = "data/raw/rda/2024/생산_2024/생산_2024.csv"
cuke_prod["missing_mask"]  = missing_mask_df(cuke_prod, prod_feat_cols)
cuke_prod["sample_id"]     = cuke_prod.apply(
    lambda r: make_sample_id(RDA_DS, f"{r['compartment_id']}:production", r["timestamp"]), axis=1)

out_cols = [c for c in SCHEMA_COLS + prod_feat_cols if c in cuke_prod.columns]
df_rda_prod = cuke_prod[out_cols].reset_index(drop=True)
save_parquet(df_rda_prod, INTERIM/"rda"/"rda_cucumber_production.parquet",
             "rda/rda_cucumber_production.parquet")

for _, r in df_rda_prod.iterrows():
    manifest_rows.append({
        "sample_id":        r["sample_id"],
        "dataset_id":       RDA_DS,
        "farm_id":          r["farm_id"],
        "compartment_id":   r["compartment_id"],
        "crop_id":          RDA_CROP,
        "season_id":        r["season_id"],
        "timestamp":        r["timestamp"],
        "available_at":     r["available_at"],
        "source_file":      "data/raw/rda/2024/생산_2024/생산_2024.csv",
        "is_harvest_event": True,
        "record_type":      "production",
    })

for orig, common, unit, freq, desc in [
    ("총출하량", "shipment_qty_g", "g",   "daily", "Total daily shipment quantity (grams)"),
    ("판매금액", "sales_krw",      "KRW", "daily", "Total sales amount (Korean won)"),
]:
    dict_rows.append({
        "dataset_id":    RDA_DS,
        "source_file":   "data/raw/rda/2024/생산_2024/생산_2024.csv",
        "original_name": orig,
        "common_name":   common,
        "unit":          unit,
        "dtype":         "float64",
        "sampling_freq": freq,
        "description":   desc,
    })

print(f"RDA done. Manifest rows so far: {len(manifest_rows):,}")

# ─── 3. Beijing 2024-25 ───────────────────────────────────────────────────────
print("=" * 60)
print("Processing Beijing 2024-25 …")

BJ_DS   = "beijing_2025"
BJ_FARM = "beijing_xiaotangshan"
BJ_CROP = "cucumber"
BJ_COMP = "bj_greenhouse_1"
BJ_SEASON = "2025_spring"
BJ_TZ     = timedelta(hours=8)   # CST → UTC

bj_file = RAW_BJ / "温室黄瓜种植监测数据（2025年3月6日~2025年7月3日）.xlsx"
xl = pd.ExcelFile(bj_file)

BJ_SHEET_MAP = {
    "空气温湿度": {   # Air temp & humidity — header row 0
        "空气温度（℃）": ("indoor_temp_c",  "°C", "5min", "Indoor air temperature"),
        "空气湿度（%）": ("indoor_rh_pct",  "%",  "5min", "Indoor relative humidity"),
    },
    "土壤墒情": {     # Soil moisture — header row 1
        "20cm土壤水分（%）": ("soil_moisture_20cm_pct", "%",  "15min", "Soil moisture at 20 cm"),
        "40cm土壤水分（%）": ("soil_moisture_40cm_pct", "%",  "15min", "Soil moisture at 40 cm"),
        "60cm土壤水分（%）": ("soil_moisture_60cm_pct", "%",  "15min", "Soil moisture at 60 cm"),
        "20cm土壤温度（℃）": ("soil_temp_20cm_c",       "°C", "15min", "Soil temperature at 20 cm"),
        "40cm土壤温度（℃）": ("soil_temp_40cm_c",       "°C", "15min", "Soil temperature at 40 cm"),
        "60cm土壤温度（℃）": ("soil_temp_60cm_c",       "°C", "15min", "Soil temperature at 60 cm"),
    },
}

SHEET_HEADER = {
    "空气温湿度": 0,
    "土壤墒情": 1,   # row 1 is actual header
}

bj_dfs = []
for sheet_name, col_map in BJ_SHEET_MAP.items():
    if sheet_name not in xl.sheet_names:
        print(f"  [skip] sheet {sheet_name} not found")
        continue
    header_row = SHEET_HEADER.get(sheet_name, 0)
    df_s = pd.read_excel(xl, sheet_name=sheet_name, header=header_row)

    # Timestamp column: 时间
    ts_col = df_s.columns[0]
    df_s["_dt"] = pd.to_datetime(df_s[ts_col], errors="coerce")
    df_s = df_s.dropna(subset=["_dt"])

    # Rename feature columns
    rename_m = {orig: v[0] for orig, v in col_map.items() if orig in df_s.columns}
    df_s = df_s.rename(columns=rename_m)
    feat = [v[0] for orig, v in col_map.items() if orig in rename_m]
    df_s = to_numeric_all(df_s, feat)

    df_s["_sheet_feat"] = json.dumps(feat)
    df_s["_feat_list"]  = str(feat)
    bj_dfs.append((df_s, feat, col_map, rename_m))

    for orig, (common, unit, freq, desc) in col_map.items():
        if orig in rename_m:
            dict_rows.append({
                "dataset_id":    BJ_DS,
                "source_file":   f"data/raw/beijing/{bj_file.name}",
                "original_name": orig,
                "common_name":   common,
                "unit":          unit,
                "dtype":         "float64",
                "sampling_freq": freq,
                "description":   desc,
            })

# Merge all sheets on timestamp
all_feat_cols = []
merged = None
for df_s, feat, col_map, rename_m in bj_dfs:
    all_feat_cols += feat
    df_s["timestamp"]    = df_s["_dt"].apply(lambda d: (d - BJ_TZ).strftime("%Y-%m-%dT%H:%M:%SZ"))
    df_s["available_at"] = df_s["timestamp"]
    if merged is None:
        merged = df_s[["timestamp", "available_at"] + feat].copy()
    else:
        merged = merged.merge(
            df_s[["timestamp"] + feat].copy(),
            on="timestamp", how="outer")

merged["dataset_id"]     = BJ_DS
merged["farm_id"]        = BJ_FARM
merged["compartment_id"] = BJ_COMP
merged["crop_id"]        = BJ_CROP
merged["season_id"]      = BJ_SEASON
merged["source_id"]      = f"data/raw/beijing/{bj_file.name}"
merged["missing_mask"]   = missing_mask_df(merged, all_feat_cols)
merged["sample_id"]      = merged["timestamp"].apply(
    lambda ts: make_sample_id(BJ_DS, BJ_COMP, ts))

out_cols = [c for c in SCHEMA_COLS + all_feat_cols if c in merged.columns]
df_bj = merged[out_cols].reset_index(drop=True)
save_parquet(df_bj, INTERIM/"beijing"/"beijing_cucumber.parquet",
             "beijing/beijing_cucumber.parquet")

for _, r in df_bj.iterrows():
    manifest_rows.append({
        "sample_id":        r["sample_id"],
        "dataset_id":       BJ_DS,
        "farm_id":          BJ_FARM,
        "compartment_id":   BJ_COMP,
        "crop_id":          BJ_CROP,
        "season_id":        BJ_SEASON,
        "timestamp":        r["timestamp"],
        "available_at":     r["available_at"],
        "source_file":      f"data/raw/beijing/{bj_file.name}",
        "is_harvest_event": False,
        "record_type":      "sensor",
    })

print(f"Beijing done. Manifest rows so far: {len(manifest_rows):,}")

# ─── 4. Write Manifest ────────────────────────────────────────────────────────
print("=" * 60)
print("Writing data_manifest.csv …")
df_manifest = pd.DataFrame(manifest_rows).drop_duplicates(subset=["sample_id"])
df_manifest.to_csv(META_DIR / "data_manifest.csv", index=False)
df_manifest.to_csv(ROOT / "data_manifest.csv", index=False)
print(f"  Manifest: {len(df_manifest):,} unique sample rows")

# ─── 5. Write Data Dictionary ─────────────────────────────────────────────────
print("Writing data_dictionary.xlsx …")
df_dict = pd.DataFrame(dict_rows).drop_duplicates(
    subset=["dataset_id", "source_file", "original_name"])

with pd.ExcelWriter(META_DIR / "data_dictionary.xlsx", engine="openpyxl") as xw:
    df_dict.to_excel(xw, sheet_name="Variables", index=False)
    for ds in df_dict["dataset_id"].unique():
        sub = df_dict[df_dict["dataset_id"] == ds]
        sub.to_excel(xw, sheet_name=ds[:31], index=False)

shutil.copy(META_DIR / "data_dictionary.xlsx", ROOT / "data_dictionary.xlsx")
print(f"  Dictionary: {len(df_dict)} variable definitions")

# ─── 6. Missingness Report ────────────────────────────────────────────────────
print("Writing missingness report …")
with open(REPORTS_DIR / "common_schema_missingness_report.txt", "w") as f:
    f.write("\n".join(report_lines))
print("  Missingness report written.")

# ─── 7. Schema Documentation ─────────────────────────────────────────────────
print("Writing docs/common_data_schema.md …")

schema_md = """\
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
"""

with open(DOCS_DIR / "common_data_schema.md", "w") as f:
    f.write(schema_md)
print("  Schema doc written.")

# ─── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("DONE. Summary:")
n_pq = len(list(INTERIM.rglob("*.parquet")))
print(f"  Interim Parquet files : {n_pq}")
print(f"  Manifest rows         : {len(df_manifest):,}")
print(f"  Dictionary entries    : {len(df_dict)}")
print(f"  Missingness report    : reports/common_schema_missingness_report.txt")
print(f"  Schema docs           : docs/common_data_schema.md")

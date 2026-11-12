#!/usr/bin/env python3
"""
Beijing 2024-2025 Greenhouse Sensor Dataset Value & Statistical Inspection

Investigates:
1. Numeric distributions, percentiles, and summary statistics across all sensor channels.
2. Raw vs Cleaned statistics (identifying the impact of -1000.0 sentinel error codes).
3. Cross-channel correlations:
   - Soil moisture at 20cm, 40cm, 60cm depths.
   - Soil temperature at 20cm, 40cm, 60cm depths.
   - Air temperature vs Air relative humidity.
4. Physical plausibility checks:
   - Air temperature ranges and extremes.
   - Relative humidity bounds [0, 100%].
   - Soil moisture volumetric bounds [0, 100%].
   - Soil temperature buffering and depth lag effects.

Outputs:
    reports/data_audit/beijing_value_inspection.txt

Run from the project root:
    python scripts/data_audit/beijing_value_inspection.py
"""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "raw" / "beijing"
REPORT_OUT = ROOT / "reports" / "data_audit" / "beijing_value_inspection.txt"

CROP_FILES = [
    {
        "crop_id": "fast_cabbage",
        "crop_name": "Fast-growing Cabbage (快菜)",
        "cultivar": "‘京研快菜’",
        "filename": "温室快菜种植监测数据（2024年12月24日~2025年2月6日）.xlsx",
        "soil_header_row": 0,
    },
    {
        "crop_id": "spring_tomato",
        "crop_name": "Spring Tomato (春茬番茄)",
        "cultivar": "‘京采8号’",
        "filename": "温室春茬番茄种植监测数据（2024年5月1日~2025年7月10日）.xlsx",
        "soil_header_row": 0,
    },
    {
        "crop_id": "autumn_tomato",
        "crop_name": "Autumn Tomato (秋茬番茄)",
        "cultivar": "‘京采8号’",
        "filename": "温室秋茬番茄种植监测数据（2024年8月28日~2025年1月10日）.xlsx",
        "soil_header_row": 0,
    },
    {
        "crop_id": "cucumber",
        "crop_name": "Cucumber (黄瓜)",
        "cultivar": "‘中农26号’",
        "filename": "温室黄瓜种植监测数据（2025年3月6日~2025年7月3日）.xlsx",
        "soil_header_row": 1,
    },
]


def print_banner(title: str, ch: str = "="):
    print("\n" + ch * 90)
    print(title)
    print(ch * 90)


def inspect_crop_values(item: dict):
    print_banner(f"CROP EXPERIMENT: {item['crop_name']} ({item['cultivar']})")
    fpath = DATA_ROOT / item["filename"]

    # -----------------------------------------------------------------
    # Air Sensor
    # -----------------------------------------------------------------
    print("\n[AIR TEMPERATURE & HUMIDITY: Greenhouse Doll II]")
    df_air = pd.read_excel(fpath, sheet_name="空气温湿度")
    df_air = df_air.dropna(axis=1, how="all")

    air_temp_col = "空气温度（℃）"
    air_rh_col = "空气湿度（%）"

    air_numeric = df_air[[air_temp_col, air_rh_col]].copy()
    stats_air = air_numeric.describe(percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]).T
    stats_air["skew"] = air_numeric.skew()
    stats_air["kurtosis"] = air_numeric.kurtosis()

    print(stats_air[["count", "mean", "std", "min", "5%", "50%", "95%", "max", "skew"]].to_string())

    corr_air = air_numeric[air_temp_col].corr(air_numeric[air_rh_col])
    print(f"\nPearson correlation Tair vs RHair: {corr_air:.4f}")
    if corr_air < -0.4:
        print("  -> Expected negative psychrometric coupling (higher T -> lower RH) observed.")

    # -----------------------------------------------------------------
    # Soil Sensor
    # -----------------------------------------------------------------
    print("\n[SOIL MOISTURE & TEMPERATURE: DZN2 Multi-Depth Probe]")
    df_soil = pd.read_excel(fpath, sheet_name="土壤墒情", header=item["soil_header_row"])
    df_soil = df_soil.dropna(axis=1, how="all")

    moisture_cols = [c for c in df_soil.columns if "水分" in c]
    temp_cols = [c for c in df_soil.columns if "温度" in c]

    # Raw stats
    print("\n--- Raw Soil Statistics (including unmasked sentinel error codes) ---")
    stats_soil_raw = df_soil[moisture_cols + temp_cols].describe(percentiles=[0.01, 0.05, 0.50, 0.95, 0.99]).T
    print(stats_soil_raw[["count", "mean", "std", "min", "50%", "max"]].to_string())

    # Cleaned stats (masking -1000.0)
    df_soil_clean = df_soil[moisture_cols + temp_cols].copy()
    for c in moisture_cols:
        df_soil_clean[c] = df_soil_clean[c].replace(-1000.0, np.nan)

    sentinel_total = (df_soil[moisture_cols] == -1000.0).sum().sum()
    if sentinel_total > 0:
        print(f"\n--- Cleaned Soil Statistics (Masked {sentinel_total} occurrences of -1000.0) ---")
        stats_soil_clean = df_soil_clean.describe(percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]).T
        stats_soil_clean["skew"] = df_soil_clean.skew()
        print(stats_soil_clean[["count", "mean", "std", "min", "5%", "50%", "95%", "max", "skew"]].to_string())
    else:
        print("\n--- No sentinel error codes detected in soil moisture stream. ---")

    # Correlations between depths
    print("\n--- Soil Moisture Cross-Depth Correlation Matrix ---")
    corr_moist = df_soil_clean[moisture_cols].corr()
    print(corr_moist.round(4).to_string())

    print("\n--- Soil Temperature Cross-Depth Correlation Matrix ---")
    corr_temp = df_soil_clean[temp_cols].corr()
    print(corr_temp.round(4).to_string())

    # Physical buffering: standard deviation decreases with depth
    print("\n--- Thermal Buffering Across Depths ---")
    for tc in temp_cols:
        print(f"  {tc}: std={df_soil_clean[tc].std():.2f} ℃, range={df_soil_clean[tc].max() - df_soil_clean[tc].min():.2f} ℃")


def main():
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as rep:
        with redirect_stdout(rep):
            print("BEIJING 2024-2025 GREENHOUSE SENSOR DATASET VALUE & STATISTICAL REPORT")
            print("Dataset DOI: 10.57760/sciencedb.agriculture.00283")
            print(f"Generated from: {Path(__file__).resolve()}")

            for item in CROP_FILES:
                inspect_crop_values(item)

    print(f"Value inspection report successfully written to {REPORT_OUT}")


if __name__ == "__main__":
    main()

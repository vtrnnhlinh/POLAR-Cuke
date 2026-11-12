#!/usr/bin/env python3
"""
Build Variable Dictionary and Inventory for Beijing Greenhouse Sensor Dataset.

Run from repository root:
    python scripts/data_audit/build_beijing_data_dictionary.py

Outputs:
    metadata/beijing_data_dictionary.csv
    reports/data_audit/beijing_inventory.txt
    reports/data_audit/beijing_file_tree.txt
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "raw" / "beijing"
CSV_OUT = ROOT / "metadata" / "beijing_data_dictionary.csv"
INV_OUT = ROOT / "reports" / "data_audit" / "beijing_inventory.txt"
TREE_OUT = ROOT / "reports" / "data_audit" / "beijing_file_tree.txt"


DEFINITIONS = [
    # Air Temperature and Humidity
    ("Greenhouse air", "空气温湿度", "时间", "时间", "Measurement timestamp (YYYY-MM-DD HH:MM:SS)", "datetime", "5 min", "raw sensor stream", "Greenhouse Doll II (温室娃娃II)", "Timestamp column for air measurements"),
    ("Greenhouse air", "空气温湿度", "空气温度", "空气温度（℃）", "Greenhouse interior air temperature", "℃", "5 min", "raw sensor stream", "Greenhouse Doll II (温室娃娃II)", "Instrument accuracy <= +/-0.2 ℃"),
    ("Greenhouse air", "空气温湿度", "空气湿度", "空气湿度（%）", "Greenhouse interior relative humidity", "%", "5 min", "raw sensor stream", "Greenhouse Doll II (温室娃娃II)", "Instrument accuracy <= +/-2 %"),

    # Soil Moisture and Temperature
    ("Greenhouse soil", "土壤墒情", "时间", "时间", "Measurement timestamp (YYYY-MM-DD HH:MM:SS)", "datetime", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Timestamp column for soil measurements; varies between 15m and 5m"),
    ("Greenhouse soil", "土壤墒情", "20cm土壤水分", "20cm土壤水分（%）", "Volumetric soil water content at 20 cm depth", "%", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-3 %; FDR probe; sentinel code -1000.0 observed on dropout"),
    ("Greenhouse soil", "土壤墒情", "40cm土壤水分", "40cm土壤水分（%）", "Volumetric soil water content at 40 cm depth", "%", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-3 %; FDR probe; sentinel code -1000.0 observed on dropout"),
    ("Greenhouse soil", "土壤墒情", "60cm土壤水分", "60cm土壤水分（%）", "Volumetric soil water content at 60 cm depth", "%", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-3 %; FDR probe; sentinel code -1000.0 observed on dropout"),
    ("Greenhouse soil", "土壤墒情", "20cm土壤温度", "20cm土壤温度（℃）", "Soil temperature at 20 cm depth", "℃", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-0.5 ℃; thermistor probe"),
    ("Greenhouse soil", "土壤墒情", "40cm土壤温度", "40cm土壤温度（℃）", "Soil temperature at 40 cm depth", "℃", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-0.5 ℃; thermistor probe"),
    ("Greenhouse soil", "土壤墒情", "60cm土壤温度", "60cm土壤温度（℃）", "Soil temperature at 60 cm depth", "℃", "15 min / 5 min", "raw sensor stream", "DZN2 Multi-Depth Probe", "Instrument accuracy <= +/-0.5 ℃; thermistor probe"),

    # Phenological stages
    ("Cultivation management", "生育期", "品种", "品种", "Crop cultivar / variety name", "text", "Per season", "metadata table", "Manual registration", "Identifies cultivar planted in experimental compartment"),
    ("Cultivation management", "生育期", "生育期", "生育期", "Phenological stage date intervals", "date range text", "Per season", "metadata table", "Manual registration", "Categorical growth stages; contains NO numerical harvest or yield mass records")
]

CROP_FILES = [
    ("Cucumber (黄瓜)", "温室黄瓜种植监测数据（2025年3月6日~2025年7月3日）.xlsx", 1),
    ("Spring Tomato (春茬番茄)", "温室春茬番茄种植监测数据（2024年5月1日~2025年7月10日）.xlsx", 0),
    ("Autumn Tomato (秋茬番茄)", "温室秋茬番茄种植监测数据（2024年8月28日~2025年1月10日）.xlsx", 0),
    ("Fast Cabbage (快菜)", "温室快菜种植监测数据（2024年12月24日~2025年2月6日）.xlsx", 0),
]


def build_inventory_and_tree():
    INV_OUT.parent.mkdir(parents=True, exist_ok=True)
    TREE_OUT.parent.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in os.listdir(DATA_ROOT) if f.endswith(".xlsx")])
    total_size = sum((DATA_ROOT / f).stat().st_size for f in files)

    with open(INV_OUT, "w", encoding="utf-8") as f:
        f.write("BEIJING GREENHOUSE SENSOR DATASET 2024-2025\n")
        f.write("Dataset Inventory\n")
        f.write("========================================\n\n")
        f.write(f"Root: data/raw/beijing/\n\n")
        f.write(f"Files: {len(files)}\n")
        f.write(f"Total size: {total_size:,} bytes\n\n")
        f.write("File list:\n")
        for fname in files:
            size = (DATA_ROOT / fname).stat().st_size
            f.write(f"- {fname} ({size:,} bytes)\n")

    with open(TREE_OUT, "w", encoding="utf-8") as f:
        f.write("BEIJING GREENHOUSE SENSOR DATASET 2024-2025\n")
        f.write("Extracted dataset directory structure\n")
        f.write("========================================\n\n")
        f.write("Root: data/raw/beijing/\n\n")
        for fname in files:
            f.write(f"f {fname}\n")


def build_dictionary():
    rows = []

    for crop_name, fname, soil_hdr in CROP_FILES:
        fpath = DATA_ROOT / fname
        if not fpath.exists():
            continue

        xl = pd.ExcelFile(fpath)

        # Air
        df_air = pd.read_excel(fpath, sheet_name="空气温湿度").dropna(axis=1, how="all")
        n_air = len(df_air)

        # Soil
        df_soil = pd.read_excel(fpath, sheet_name="土壤墒情", header=soil_hdr).dropna(axis=1, how="all")
        n_soil = len(df_soil)

        # Stage
        df_stage = pd.read_excel(fpath, sheet_name="生育期", header=None)
        n_stage = len(df_stage)

        for scope, sheet_name, readme_var, actual_col, desc, unit, freq, dtype, collector, notes in DEFINITIONS:
            if sheet_name == "空气温湿度":
                observed_rows = n_air
                timestamp_col = "时间"
                if actual_col in df_air.columns:
                    missing_cells = int(df_air[actual_col].isna().sum())
                    semantic_status = "matched"
                else:
                    missing_cells = 0
                    semantic_status = "missing"
            elif sheet_name == "土壤墒情":
                observed_rows = n_soil
                timestamp_col = "时间"
                if actual_col in df_soil.columns:
                    # check for sentinel code in missing count note
                    missing_cells = int(df_soil[actual_col].isna().sum())
                    neg_sentinels = int((df_soil[actual_col] == -1000.0).sum()) if np.issubdtype(df_soil[actual_col].dtype, np.number) else 0
                    if neg_sentinels > 0:
                        notes += f"; contains {neg_sentinels} unmasked -1000.0 sentinel error values"
                    semantic_status = "matched"
                else:
                    missing_cells = 0
                    semantic_status = "missing"
            else:
                observed_rows = n_stage
                timestamp_col = "None (text stages)"
                missing_cells = 0
                semantic_status = "matched"

            missing_pct = round(missing_cells / observed_rows * 100, 4) if observed_rows > 0 else 0.0

            rows.append({
                "crop": crop_name,
                "file": fname,
                "sheet": sheet_name,
                "scope": scope,
                "variable": readme_var,
                "actual_column": actual_col,
                "description": desc,
                "unit": unit,
                "documented_frequency": freq,
                "dataset_type": dtype,
                "sensor_hardware": collector,
                "observed_rows": observed_rows,
                "missing_cells": missing_cells,
                "missing_percent": missing_pct,
                "timestamp_column_in_file": timestamp_col,
                "semantic_status": semantic_status,
                "notes": notes
            })

    df_out = pd.DataFrame(rows)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print(f"Data dictionary written to {CSV_OUT} ({len(df_out)} rows)")


def main():
    build_inventory_and_tree()
    build_dictionary()


if __name__ == "__main__":
    main()

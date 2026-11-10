#!/usr/bin/env python3
"""
Build a variable dictionary for the WUR Autonomous Greenhouse Challenge dataset.

Run from the repository root:
    python scripts/data_audit/build_wur_data_dictionary.py

Outputs:
    metadata/wur_data_dictionary.csv
    reports/data_audit/wur_readme_audit_comparison.md

Requires:
    pandas
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "raw" / "wur"
CSV_OUT = ROOT / "metadata" / "wur_data_dictionary.csv"
MD_OUT = ROOT / "reports" / "data_audit" / "wur_readme_audit_comparison.md"

# Definitions transcribed from ReadMe.pdf. Keep the README wording/units;
# unresolved wording is flagged in notes rather than silently corrected.
DEFINITIONS = [
    # Weather station
    ("meteo.csv", "Tout", "outside temperature", "°C", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Rhout", "outside Relative Humidity", "%", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Iglob", "radiation", "W/m2", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Windsp", "wind speed", "m/s", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "RadSum", "radiation sum", "J/cm2", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Winddir", "wind direction", "0-360?", "5 min", "raw data", "Weather station", "README unit is written as '0-360?'; verify the intended unit."),
    ("meteo.csv", "Rain", "rain (status 1=rain, 0=dry)", "1=rain, 0=dry", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "PARout", "PAR weather measurement", "µmol/m²/s", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Pyrgeo", "heat emission: pyrgeometer", "W/m2", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "AbsHumOut", "absolute humidity content outside air", "g/m3", "5 min", "raw data", "Weather station", ""),
    ("meteo.csv", "Time", "Timestamp 5 minute (Excel format)", "", "5 min", "raw data", "Weather station", "Timestamp column."),

    # Greenhouse climate
    ("Greenhouse_climate.csv", "Tair", "Air temperature greenhouse", "°C", "5 min", "raw data", "Measuring box", ""),
    ("Greenhouse_climate.csv", "RHair", "Relative humidity greenhouse", "%", "5 min", "raw data", "Measuring box", ""),
    ("Greenhouse_climate.csv", "CO2air", "CO2 greenhouse", "ppm", "5 min", "raw data", "Measuring box", ""),
    ("Greenhouse_climate.csv", "HumDef", "Humidity deficit", "g/m3", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "VentLee", "Vent lee", "% (0-100)", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "Ventwind", "Vent wind", "% (0-100)", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "AssimLight", "Assimilation lighting", "% (0-100)", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "EnScr", "Energy curtain", "% (0-100)", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "BlackScr", "Black-out curtain", "% (0-100)", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "PipeLow", "Lower circuit Temperature", "°C", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "PipeGrow", "Growth circuit Temperature", "°C", "5 min", "raw data", "Process computer", ""),
    ("Greenhouse_climate.csv", "GHtime", "Timestamp 5 minute (Excel format)", "", "5 min", "raw data", "Process computer", "Timestamp column."),

    # Irrigation
    ("Irrigation.csv", "Water", "Irrigation water supplied", "L/m2", "Daily", "Processed", "", "README comment: 'Time between last and next irrigation turn'; wording is ambiguous."),
    ("Irrigation.csv", "Drain", "Drainage water", "L/m2", "Daily", "Processed", "", ""),
    ("Irrigation.csv", "pH_Drain", "pH of drainage water", "[-]", "Daily", "Processed", "pH Probes", "README says daily averages on 5-minute data."),
    ("Irrigation.csv", "EC_Drain", "EC of drainage water", "dS/m", "Daily", "Processed", "EC Probes", "README says daily averages on 5-minute data."),
    ("Irrigation.csv", "Time", "Timestamp 1 day (Excel format)", "", "Daily", "Processed", "", "Timestamp column."),

    # VIP / control setpoints
    ("vip.csv", "CO2_VIP", "CO2 setpoint", "ppm", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "HumDef_Vip", "humidity deficit setpoint", "g/kg", "5 min", "raw data", "Process computer", "Do not conflate with climate HumDef (g/m3)."),
    ("vip.csv", "MinPipeLow_Vip", "net pipe minimum temperature setpoint", "°C", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "MinPipeGrow_Vip", "crop pipe minimum temperature setpoint", "°C", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "HeatTemp_VIP", "heating temperature setpoint", "°C", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "VentLeew_VIP", "ventilation temperature lee side setpoint", "°C", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "VentLeewMin_VIP", "lee side window position minimum setpoint", "%", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "VentWind_VIP", "ventilation temperature wind side setpoint", "°C", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "WaterSupInt_VIP", "water supply interval time setpoint", "minutes", "5 min", "raw data", "Process computer", ""),
    ("vip.csv", "Time", "Timestamp 5 minute (Excel format)", "", "5 min", "raw data", "Process computer", "Timestamp column; AiCU indexed columns require separate index interpretation."),

    # Resource calculations
    ("ResourceCalculations.csv", "Heating _Eenrgy", "Heating energy consumption (rail+ grow pipes)", "KWh/m2 day", "Daily", "Processed", "", "README spelling retained; actual CSV header may differ."),
    ("ResourceCalculations.csv", "Electricity _Lamps", "Electricity consumption (artificial light)", "KWh/m2 day", "Daily", "Processed", "", "README spelling retained; actual CSV header may differ."),
    ("ResourceCalculations.csv", "CO2_dosage", "CO2 consumption", "Kg/m2 day", "Daily", "Processed", "", "README says derived from cumulative valve-open time and dosing capacity."),
    ("ResourceCalculations.csv", "net_water", "Water use (net of drainage)", "L/m2 day", "Daily", "Processed", "", "README defines as irrigation minus Drain."),
    ("ResourceCalculations.csv", "Labour", "Labour hours for crop management and harvest", "hours/day", "Daily", "Processed", "", "README describes a 0.42 correction factor for the small-scale greenhouse."),
    ("ResourceCalculations.csv", "Time", "Timestamp 1 day (Excel format)", "", "Daily", "Processed", "", "Timestamp column."),

    # Production
    ("Production.csv", "Prod_value_cum", "Production value (fruit number multiplied by price)", "€", "Daily", "Processed", "Manual registration", ""),
    ("Production.csv", "ProdA_cum", "Cumulative Production cucumber category A", "Kg/m2", "Daily", "Processed", "Manual registration", "Strong candidate target; cumulative mass."),
    ("Production.csv", "ProdB_cum", "Cumulative Production cucumber category B", "Kg/m2", "Daily", "Processed", "Manual registration", "Strong candidate target; cumulative mass."),
    ("Production.csv", "ProdA_num", "Cumulative number of cucumber category A", "number of fruits", "Daily", "Processed", "Manual registration", "Audit observed fractional values and decreases; conflicts with documented cumulative-count behavior."),
    ("Production.csv", "ProdB_num", "Cumulative number of cucumber category B", "number of fruits", "Daily", "Processed", "Manual registration", "Audit observed fractional values and decreases; conflicts with documented cumulative-count behavior."),
    ("Production.csv", "Total_Prod_cum", "Total cumulative production", "Kg/m2", "Daily", "Processed", "Manual registration", "README says sum of class A and class B; audit confirms equality."),
    ("Production.csv", "time", "Timestamp 1 day (Excel format)", "", "Daily", "Processed", "", "Timestamp column."),

    # Crop management
    ("CropManagement.csv", "Fruit maintained", "% of fruit mainatained on internode", "%", "week", "raw", "Manual registration", "README spelling retained; actual CSV header may differ."),
    ("CropManagement.csv", "Leaves mainatained", "% of leaves mainatained on internode", "%", "week", "raw", "Manual registration", "README spelling retained; actual CSV header may differ."),
    ("CropManagement.csv", "Stem_Elong", "stem-elongation", "cm/week", "week", "raw", "Manual registration", ""),
    ("CropManagement.csv", "FruitGrw", "fruit development time", "days/fruit", "week", "raw", "Manual registration", ""),
    ("CropManagement.csv", "LeafFormRate", "Leaf formation rate", "n_leaves/stem week", "week", "raw", "Manual registration", ""),
    ("CropManagement.csv", "N_leaves", "Cumulative number of leaves", "n_leaves/stem", "week", "raw", "Manual registration", ""),
    ("CropManagement.csv", "Weeks", "Timestamp week number (year 2018)", "", "week", "raw", "", "Weekly time identifier."),
]

# README header variants / spelling differences. Normalization is used only
# to match a documented name to a real header; it does not alter source files.
ALIASES = {
    ("ResourceCalculations.csv", "Heating _Eenrgy"): ["Heating_Energy", "Heating_Eenrgy", "Heating _Eenrgy"],
    ("ResourceCalculations.csv", "Electricity _Lamps"): ["Electricity_Lamps", "Electricity _Lamps"],
    ("CropManagement.csv", "Fruit maintained"): ["Fruit maintained", "FruitMaintained", "Fruit_maintained"],
    ("CropManagement.csv", "Leaves mainatained"): ["Leaves mainatained", "LeavesMaintained", "Leaves_maintained"],
}

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

def read_csv(path: Path) -> pd.DataFrame:
    # Preserve original CSVs; only read into memory.
    return pd.read_csv(path, encoding="utf-8-sig")

def timestamp_column(filename: str, columns: list[str]) -> str | None:
    candidates = {
        "Greenhouse_climate.csv": ["GHtime"],
        "Production.csv": ["time"],
        "Irrigation.csv": ["Time", "time"],
        "ResourceCalculations.csv": ["Time", "time"],
        "vip.csv": ["Time", "time"],
        "CropManagement.csv": ["Weeks", "weeks"],
        "meteo.csv": ["Time", "time"],
    }.get(filename, [])
    lookup = {norm(c): c for c in columns}
    for candidate in candidates:
        if norm(candidate) in lookup:
            return lookup[norm(candidate)]
    return None

def find_actual_column(filename: str, readme_name: str, columns: list[str]) -> str | None:
    candidates = ALIASES.get((filename, readme_name), []) + [readme_name]
    lookup = {norm(c): c for c in columns}
    for candidate in candidates:
        if norm(candidate) in lookup:
            return lookup[norm(candidate)]
    return None

def main() -> int:
    if not DATA_ROOT.exists():
        print(f"Dataset directory not found: {DATA_ROOT}", file=sys.stderr)
        return 1

    team_dirs = sorted(p for p in DATA_ROOT.iterdir() if p.is_dir())
    scopes: list[tuple[str, Path, str]] = []
    meteo = DATA_ROOT / "meteo.csv"
    if meteo.exists():
        scopes.append(("Weather station", meteo, "meteo.csv"))
    for team_dir in team_dirs:
        for filename in [
            "Greenhouse_climate.csv", "Irrigation.csv", "vip.csv",
            "ResourceCalculations.csv", "Production.csv", "CropManagement.csv"
        ]:
            path = team_dir / filename
            if path.exists():
                scopes.append((team_dir.name, path, filename))

    rows: list[dict] = []
    matched_actual: dict[tuple[str, str], set[str]] = {}

    for scope_name, path, filename in scopes:
        df = read_csv(path)
        ts_col = timestamp_column(filename, list(df.columns))
        for definition in [d for d in DEFINITIONS if d[0] == filename]:
            _, readme_var, description, unit, frequency, dataset_type, collection, notes = definition
            actual = find_actual_column(filename, readme_var, list(df.columns))
            missing = int(df[actual].isna().sum()) if actual else None
            matched_actual.setdefault((scope_name, filename), set())
            if actual:
                matched_actual[(scope_name, filename)].add(actual)
            rows.append({
                "scope": scope_name,
                "file": filename,
                "readme_variable": readme_var,
                "actual_column": actual or "",
                "description_from_readme": description,
                "unit_from_readme": unit,
                "documented_frequency": frequency,
                "dataset_type": dataset_type,
                "data_collection": collection,
                "observed_rows": len(df),
                "missing_cells": missing if actual else "",
                "missing_percent": round(missing / len(df) * 100, 4) if actual and len(df) else "",
                "timestamp_column_in_file": ts_col or "",
                "semantic_status": (
                    "matched" if actual else "not matched; check header spelling/schema"
                ),
                "notes": notes,
            })

        # Include any real CSV columns not represented in the README dictionary.
        documented_names = {
            norm(d[1]) for d in DEFINITIONS if d[0] == filename
        }
        documented_names.update(
            norm(alias)
            for (alias_file, _), aliases in ALIASES.items()
            if alias_file == filename
            for alias in aliases
        )
        for col in df.columns:
            if norm(col) not in documented_names:
                rows.append({
                    "scope": scope_name,
                    "file": filename,
                    "readme_variable": "",
                    "actual_column": col,
                    "description_from_readme": "",
                    "unit_from_readme": "",
                    "documented_frequency": "",
                    "dataset_type": "",
                    "data_collection": "",
                    "observed_rows": len(df),
                    "missing_cells": int(df[col].isna().sum()),
                    "missing_percent": round(df[col].isna().mean() * 100, 4),
                    "timestamp_column_in_file": ts_col or "",
                    "semantic_status": "present in CSV; no exact README dictionary entry",
                    "notes": "Requires manual semantic mapping.",
                })

    if not rows:
        print("No matching CSV files found under the dataset directory.", file=sys.stderr)
        return 1

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    dictionary = pd.DataFrame(rows)
    dictionary.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

    # Produce a concise comparison report from actual files.
    lines = [
        "# WUR README–Audit Comparison",
        "",
        "Generated by `scripts/data_audit/build_wur_data_dictionary.py`.",
        "",
        "This report compares definitions transcribed from `ReadMe.pdf` with the current CSV headers,",
        "row counts, and missingness. It does not infer undocumented physical meanings.",
        "",
        "## Dataset coverage",
        "",
        f"- Team directories found: **{len(team_dirs)}** ({', '.join(p.name for p in team_dirs)})",
        f"- CSV files inspected: **{len(scopes)}** (including `meteo.csv` when present)",
        f"- Data dictionary rows: **{len(dictionary)}**",
        "",
        "## Documented variable matching",
        "",
    ]
    summary = (
        dictionary.groupby(["file", "semantic_status"], dropna=False)
        .size().unstack(fill_value=0)
    )
    lines.append("| File | " + " | ".join(summary.columns) + " |")
    lines.append("|---|" + "|".join(["---:"] * len(summary.columns)) + "|")
    for filename, row in summary.iterrows():
        lines.append("| " + filename + " | " + " | ".join(str(int(row[c])) for c in summary.columns) + " |")

    lines += [
        "",
        "## Key interpretation points from the README and prior audit",
        "",
        "### Production variables",
        "",
        "- `ProdA_cum` and `ProdB_cum` are documented as cumulative category A/B production in **kg/m²**.",
        "- `Total_Prod_cum` is documented as total cumulative production, the sum of A and B.",
        "- `ProdA_num` and `ProdB_num` are documented as **cumulative fruit counts**. The prior numerical audit observed fractional values and decreases; this is a documentation–observation conflict, not grounds to relabel them as interval counts.",
        "- `Prod_value_cum` is documented as production value in **€**, calculated from fruit number multiplied by price.",
        "- Daily increments of cumulative mass are candidate targets, but the first difference is undefined and negative increments must be investigated.",
        "",
        "### Temporal resolutions",
        "",
        "- Greenhouse climate, VIP setpoints, and weather-station observations: **5 minutes** in the README.",
        "- Irrigation, resource calculations, and production: **daily** in the README.",
        "- Crop management: **weekly** in the README.",
        "- Do not expand daily or weekly variables to five-minute rows without an explicit alignment policy.",
        "",
        "### Important schema and semantic issues",
        "",
        "- AiCU's indexed VIP columns are structurally different from the other teams' unsuffixed VIP variables. The README defines the underlying control families but does not explain the suffix/index meaning.",
        "- `HumDef` is documented in **g/m³**, while `HumDef_Vip` is documented in **g/kg**; preserve this distinction.",
        "- `BlackScr` is a documented blackout-curtain position (%), but the prior audit found it 100% missing for DeepGreens. The cause is not documented.",
        "- The README's `Water` comment ('Time between last and next irrigation turn') is ambiguous relative to its description and L/m² unit.",
        "- The README's `Winddir` unit is printed as `0-360?`; verify the intended unit.",
        "- Resource variables such as `net_water` are derived quantities; avoid treating them as independent of their source measurements without considering the derivation.",
        "",
        "## Missingness by documented variable",
        "",
        "Missingness below is computed from the CSVs currently present. It is not an imputation recommendation.",
        "",
    ]
    miss = dictionary[dictionary["missing_percent"].apply(lambda x: str(x).strip() != "")]
    if not miss.empty:
        lines += ["| Scope | File | Variable | Missing | Missing % |",
                  "|---|---|---|---:|---:|"]
        for _, r in miss[miss["missing_cells"].astype(str).astype(bool)].iterrows():
            if float(r["missing_cells"]) > 0:
                lines.append(
                    f"| {r['scope']} | {r['file']} | {r['actual_column'] or r['readme_variable']} | "
                    f"{int(float(r['missing_cells']))} | {float(r['missing_percent']):.4f}% |"
                )
    else:
        lines.append("No matching documented variables were available for missingness calculation.")

    lines += [
        "",
        "## Limits of this comparison",
        "",
        "- README definitions are transcribed as written; spelling and ambiguous units/comments are not silently corrected.",
        "- Header matching uses conservative normalization and a small alias list. Unmatched columns are retained in the CSV with `semantic_status` indicating that manual mapping is needed.",
        "- The README does not establish the physical compartment ID represented by each team directory.",
        "- The README does not explain the AiCU VIP indices or the cause of missing DeepGreens `BlackScr` values.",
        "",
        "## Outputs",
        "",
        f"- Data dictionary: `{CSV_OUT.relative_to(ROOT)}`",
        f"- This report: `{MD_OUT.relative_to(ROOT)}`",
        "",
    ]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated: {CSV_OUT}")
    print(f"Generated: {MD_OUT}")
    print(f"Dictionary rows: {len(dictionary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

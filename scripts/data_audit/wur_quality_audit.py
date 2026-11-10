#!/usr/bin/env python3

"""
WUR Dataset Quality Audit

Investigates:
1. Missing values per column and team.
2. Duplicate timestamps.
3. Missing five-minute greenhouse climate intervals.
4. Missing daily production observations.
5. Negative differences in cumulative production.
6. Consistency of Total_Prod_cum = ProdA_cum + ProdB_cum.
7. Behavior of ProdA_num and ProdB_num.
8. Schema differences between teams, especially vip.csv.

Output:
    reports/data_audit/wur_quality_report.txt

Run from the project root:
    python scripts/data_audit/wur_quality_audit.py
"""

from pathlib import Path
from contextlib import redirect_stdout
import pandas as pd
import numpy as np


# ============================================================
# Configuration
# ============================================================

ROOT = Path("data/raw/wur")
OUTPUT = Path("reports/data_audit/wur_quality_report.txt")

CLIMATE_FILE = "Greenhouse_climate.csv"
PRODUCTION_FILE = "Production.csv"

CLIMATE_TIMESTAMP = "GHtime"
PRODUCTION_TIMESTAMP = "time"

CUMULATIVE_COLUMNS = [
    "ProdA_cum",
    "ProdB_cum",
    "Total_Prod_cum",
]

COUNT_COLUMNS = [
    "ProdA_num",
    "ProdB_num",
]

NUMERIC_TOLERANCE = 1e-6


# ============================================================
# Utility functions
# ============================================================

def read_csv(path):
    """Read a CSV file without modifying the original."""
    return pd.read_csv(path, encoding="utf-8-sig")


def parse_timestamp(series):
    """
    Parse timestamps.

    The WUR README documents Excel serial timestamps.
    Numeric values in a plausible Excel date range are
    interpreted using the Excel origin 1899-12-30.

    Otherwise, attempt normal datetime parsing.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().all() and len(numeric) > 0:
        if numeric.between(20000, 80000).all():
            return pd.to_datetime(
                numeric,
                unit="D",
                origin="1899-12-30",
                errors="coerce",
            )

    return pd.to_datetime(series, errors="coerce")


def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


def find_timestamp_column(df):
    """Find a likely timestamp column, ignoring case."""
    candidates = ["time", "ghtime", "timestamp", "datetime"]

    column_map = {col.lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate in column_map:
            return column_map[candidate]

    return None


# ============================================================
# 1. Missing values
# ============================================================

def audit_missing_values(teams):
    print_section("1. MISSING VALUES PER COLUMN AND TEAM")

    for team in teams:
        print(f"\nTEAM: {team.name}")

        for path in sorted(team.glob("*.csv")):
            df = read_csv(path)

            missing = df.isna().sum()
            missing = missing[missing > 0]

            print(f"\n  FILE: {path.name}")
            print(f"  Rows: {len(df):,}")
            print(f"  Total missing cells: {int(df.isna().sum().sum()):,}")

            if missing.empty:
                print("  No missing values detected.")
            else:
                for column, count in missing.items():
                    percentage = count / len(df) * 100 if len(df) else 0

                    print(
                        f"  {column}: {count:,} "
                        f"({percentage:.2f}%)"
                    )


# ============================================================
# 2. Duplicate timestamps
# ============================================================

def audit_duplicate_timestamps(teams):
    print_section("2. DUPLICATE TIMESTAMPS")

    for team in teams:
        print(f"\nTEAM: {team.name}")

        for path in sorted(team.glob("*.csv")):
            df = read_csv(path)
            timestamp_col = find_timestamp_column(df)

            if timestamp_col is None:
                continue

            timestamps = parse_timestamp(df[timestamp_col])
            valid = timestamps.dropna()

            duplicates = valid.duplicated(keep=False)
            duplicate_rows = int(duplicates.sum())
            duplicate_values = int(
                valid[valid.duplicated()].nunique()
            )

            print(f"\n  FILE: {path.name}")
            print(f"  Timestamp column: {timestamp_col}")
            print(f"  Invalid timestamps: {timestamps.isna().sum()}")
            print(f"  Rows involved in duplicates: {duplicate_rows}")
            print(f"  Duplicate timestamp values: {duplicate_values}")


# ============================================================
# 3. Missing five-minute climate intervals
# ============================================================

def audit_climate_intervals(teams):
    print_section("3. MISSING FIVE-MINUTE CLIMATE INTERVALS")

    for team in teams:
        path = team / CLIMATE_FILE

        print(f"\nTEAM: {team.name}")

        if not path.exists():
            print("  Climate file not found.")
            continue

        df = read_csv(path)

        if CLIMATE_TIMESTAMP not in df.columns:
            print(f"  Missing timestamp column: {CLIMATE_TIMESTAMP}")
            continue

        timestamps = parse_timestamp(df[CLIMATE_TIMESTAMP])

        # Excel serial dates introduce tiny floating-point errors.
        # Normalize timestamps to their documented 5-minute resolution.
        timestamps = (
            timestamps
            .dropna()
            .dt.round("5min")
            .sort_values()
        )

        if timestamps.empty:
            print("  No valid timestamps.")
            continue

        observed = pd.DatetimeIndex(timestamps.unique()).sort_values()

        expected = pd.date_range(
            start=observed.min(),
            end=observed.max(),
            freq="5min",
        )

        missing = expected.difference(observed)

        # Detect gaps between consecutive observations.
        intervals = observed.to_series().diff().dropna()
        gaps = intervals[intervals > pd.Timedelta(minutes=5)]

        print(f"  First timestamp: {observed.min()}")
        print(f"  Last timestamp:  {observed.max()}")
        print(f"  Observed unique timestamps: {len(observed):,}")
        print(f"  Expected timestamps: {len(expected):,}")
        print(f"  Missing five-minute timestamps: {len(missing):,}")

        if len(expected):
            percentage = len(missing) / len(expected) * 100
            print(f"  Missing interval percentage: {percentage:.4f}%")

        print(f"  Gaps larger than five minutes: {len(gaps):,}")

        if not missing.empty:
            print("  First 10 missing timestamps:")
            for timestamp in missing[:10]:
                print(f"    {timestamp}")

        if not gaps.empty:
            print("  First 10 observed gaps:")
            for timestamp, interval in gaps.head(10).items():
                print(f"    Ending at {timestamp}: {interval}")


# ============================================================
# 4. Missing daily production observations
# ============================================================

def audit_production_dates(teams):
    print_section("4. MISSING DAILY PRODUCTION OBSERVATIONS")

    for team in teams:
        path = team / PRODUCTION_FILE

        print(f"\nTEAM: {team.name}")

        if not path.exists():
            print("  Production file not found.")
            continue

        df = read_csv(path)

        if PRODUCTION_TIMESTAMP not in df.columns:
            print(f"  Missing timestamp column: {PRODUCTION_TIMESTAMP}")
            continue

        timestamps = parse_timestamp(df[PRODUCTION_TIMESTAMP])
        valid = timestamps.dropna()

        if valid.empty:
            print("  No valid production timestamps.")
            continue

        dates = pd.DatetimeIndex(valid.dt.normalize().unique()).sort_values()

        expected = pd.date_range(
            start=dates.min(),
            end=dates.max(),
            freq="D",
        )

        missing = expected.difference(dates)

        print(f"  First date: {dates.min().date()}")
        print(f"  Last date:  {dates.max().date()}")
        print(f"  Observed unique dates: {len(dates)}")
        print(f"  Expected calendar dates: {len(expected)}")
        print(f"  Missing dates: {len(missing)}")

        if len(expected):
            percentage = len(missing) / len(expected) * 100
            print(f"  Missing date percentage: {percentage:.4f}%")

        if not missing.empty:
            print("  Missing dates:")
            for date in missing:
                print(f"    {date.date()}")


# ============================================================
# 5. Negative differences in cumulative production
# ============================================================

def audit_cumulative_production(teams):
    print_section("5. NEGATIVE DIFFERENCES IN CUMULATIVE PRODUCTION")

    for team in teams:
        path = team / PRODUCTION_FILE

        print(f"\nTEAM: {team.name}")

        if not path.exists():
            continue

        df = read_csv(path)

        if PRODUCTION_TIMESTAMP in df.columns:
            df["_timestamp"] = parse_timestamp(
                df[PRODUCTION_TIMESTAMP]
            )
            df = df.sort_values("_timestamp")

        for column in CUMULATIVE_COLUMNS:
            if column not in df.columns:
                print(f"\n  {column}: COLUMN NOT FOUND")
                continue

            values = pd.to_numeric(df[column], errors="coerce")
            differences = values.diff()

            negative = differences[differences < -NUMERIC_TOLERANCE]

            print(f"\n  {column}")
            print(f"    Valid values: {values.notna().sum()}")
            print(f"    Negative differences: {len(negative)}")
            print(f"    Missing differences: {differences.isna().sum()}")
            print(f"    Minimum difference: {differences.min()}")
            print(f"    Maximum difference: {differences.max()}")

            if not negative.empty:
                print("    First negative differences:")
                for index, value in negative.head(10).items():
                    print(f"      Row {index}: {value}")


# ============================================================
# 6. Production total consistency
# ============================================================

def audit_production_consistency(teams):
    print_section(
        "6. TOTAL_PROD_CUM = ProdA_cum + ProdB_cum"
    )

    for team in teams:
        path = team / PRODUCTION_FILE

        print(f"\nTEAM: {team.name}")

        if not path.exists():
            continue

        df = read_csv(path)

        required = [
            "ProdA_cum",
            "ProdB_cum",
            "Total_Prod_cum",
        ]

        if not all(col in df.columns for col in required):
            print("  Required production columns are missing.")
            continue

        a = pd.to_numeric(df["ProdA_cum"], errors="coerce")
        b = pd.to_numeric(df["ProdB_cum"], errors="coerce")
        total = pd.to_numeric(df["Total_Prod_cum"], errors="coerce")

        expected = a + b
        difference = (total - expected).abs()

        valid = difference.notna()
        mismatches = difference[valid] > NUMERIC_TOLERANCE

        print(f"  Comparable observations: {valid.sum()}")
        print(f"  Matching observations: {(~mismatches).sum()}")
        print(f"  Mismatching observations: {mismatches.sum()}")

        if valid.any():
            print(f"  Maximum absolute difference: {difference[valid].max():.10f}")
            print(f"  Mean absolute difference: {difference[valid].mean():.10f}")

        if mismatches.any():
            print("  First mismatches:")
            for index in difference[mismatches].head(10).index:
                print(
                    f"    Row {index}: "
                    f"A={a.loc[index]}, "
                    f"B={b.loc[index]}, "
                    f"Total={total.loc[index]}, "
                    f"Error={difference.loc[index]}"
                )


# ============================================================
# 7. Behavior of ProdA_num and ProdB_num
# ============================================================

def audit_production_counts(teams):
    print_section(
        "7. BEHAVIOR OF ProdA_num AND ProdB_num"
    )

    for team in teams:
        path = team / PRODUCTION_FILE

        print(f"\nTEAM: {team.name}")

        if not path.exists():
            continue

        df = read_csv(path)

        if PRODUCTION_TIMESTAMP in df.columns:
            df["_timestamp"] = parse_timestamp(
                df[PRODUCTION_TIMESTAMP]
            )
            df = df.sort_values("_timestamp")

        for column in COUNT_COLUMNS:
            if column not in df.columns:
                print(f"\n  {column}: COLUMN NOT FOUND")
                continue

            values = pd.to_numeric(df[column], errors="coerce").dropna()
            differences = values.diff().dropna()

            if values.empty:
                print(f"\n  {column}: NO VALID VALUES")
                continue

            negative = int((differences < -NUMERIC_TOLERANCE).sum())
            positive = int((differences > NUMERIC_TOLERANCE).sum())
            zero = int((differences.abs() <= NUMERIC_TOLERANCE).sum())

            monotonic_ratio = (
                (differences >= -NUMERIC_TOLERANCE).mean()
                if len(differences) else float("nan")
            )

            integer_ratio = np.isclose(
                values,
                np.round(values),
                atol=NUMERIC_TOLERANCE,
            ).mean()

            print(f"\n  {column}")
            print(f"    Number of valid values: {len(values)}")
            print(f"    Minimum: {values.min()}")
            print(f"    Maximum: {values.max()}")
            print(f"    Negative differences: {negative}")
            print(f"    Positive differences: {positive}")
            print(f"    Zero differences: {zero}")
            print(f"    Non-decreasing difference ratio: {monotonic_ratio:.2%}")
            print(f"    Integer-like value ratio: {integer_ratio:.2%}")

            if len(differences) and monotonic_ratio >= 0.98:
                print("    Heuristic: CUMULATIVE-LIKE behavior")
            elif len(differences):
                print("    Heuristic: NON-CUMULATIVE / INTERVAL-LIKE behavior")
            else:
                print("    Heuristic: INSUFFICIENT OBSERVATIONS")

            if integer_ratio < 0.95:
                print(
                    "    WARNING: Values are mostly non-integer. "
                    "Do not interpret them as literal fruit counts "
                    "without further documentation."
                )

            print("    First 10 values:", values.head(10).tolist())
            print("    Last 10 values: ", values.tail(10).tolist())


# ============================================================
# 8. Schema comparison
# ============================================================

def audit_schemas(teams):
    print_section("8. SCHEMA DIFFERENCES BETWEEN TEAMS")

    filenames = sorted({
        path.name
        for team in teams
        for path in team.glob("*.csv")
    })

    for filename in filenames:
        print(f"\nFILE: {filename}")

        schemas = {}

        for team in teams:
            path = team / filename

            if not path.exists():
                print(f"  {team.name}: FILE MISSING")
                continue

            df = read_csv(path)
            schemas[team.name] = list(df.columns)

        if not schemas:
            continue

        all_columns = set().union(
            *(set(columns) for columns in schemas.values())
        )

        common_columns = set.intersection(
            *(set(columns) for columns in schemas.values())
        )

        print(f"  Teams containing file: {len(schemas)}")
        print(f"  Union of columns: {len(all_columns)}")
        print(f"  Common columns: {len(common_columns)}")

        for team_name, columns in schemas.items():
            missing = all_columns - set(columns)
            extra = set(columns) - common_columns

            print(f"\n  {team_name}: {len(columns)} columns")
            print(f"    Missing relative to union: {sorted(missing)}")
            print(f"    Unique relative to intersection: {sorted(extra)}")

        if filename.lower() == "vip.csv":
            print("\n  VIP SCHEMA COMPARISON")

            for team_name, columns in schemas.items():
                print(f"    {team_name}: {len(columns)} columns")
                print(f"      {columns}")

            if "AiCU" in schemas:
                other_columns = set().union(
                    *[
                        set(columns)
                        for name, columns in schemas.items()
                        if name != "AiCU"
                    ]
                )

                aicu_columns = set(schemas["AiCU"])

                print("\n    AiCU-specific columns:")
                print(f"      {sorted(aicu_columns - other_columns)}")

                print("\n    Columns present in other teams but not AiCU:")
                print(f"      {sorted(other_columns - aicu_columns)}")


# ============================================================
# Main
# ============================================================

def main():
    if not ROOT.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {ROOT.resolve()}"
        )

    teams = sorted(
        path for path in ROOT.iterdir()
        if path.is_dir()
    )

    if not teams:
        raise RuntimeError(f"No team directories found in {ROOT}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as report:
        with redirect_stdout(report):

            print("WUR DATASET QUALITY AUDIT")
            print("=" * 90)
            print(f"Dataset: {ROOT.resolve()}")
            print(f"Generated: {pd.Timestamp.now()}")
            print(f"Teams inspected: {len(teams)}")
            print(f"Team names: {[team.name for team in teams]}")
            print("=" * 90)

            audit_missing_values(teams)
            audit_duplicate_timestamps(teams)
            audit_climate_intervals(teams)
            audit_production_dates(teams)
            audit_cumulative_production(teams)
            audit_production_consistency(teams)
            audit_production_counts(teams)
            audit_schemas(teams)

    print(f"Quality audit completed: {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()

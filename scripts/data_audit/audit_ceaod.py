#!/usr/bin/env python3
"""Exploratory quality audit for the CEAOD GreenhouseCucumber time series.

Designed for HiPower_NL_2018-08_2018-12.csv:
- timestamp and sampling-interval integrity
- missingness by column and consecutive missing runs
- schema/type inventory and descriptive statistics
- climate, actuator, setpoint, irrigation, energy and weather variable profiles
- conservative domain checks for selected variables

The script does not modify the source CSV. Domain checks are screening rules,
not proof that a value is scientifically invalid.
"""

import argparse
import csv
import hashlib
import io
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

TIME_COLUMN = "Timestamp"
DEFAULT_INPUT = "data/raw/GreenhouseCucumber/HiPower_NL_2018-08_2018-12.csv"
# Broad groups based on the supplied header. These are descriptive groupings,
# not authoritative definitions of the variables.
GROUP_RULES = {
    "indoor_climate": ("temp", "rh", "co2", "humiditydeficit"),
    "ventilation_heating": ("vent", "heating", "circuit", "pipe"),
    "screens_lighting": ("curtain", "screen", "doek", "lighting", "lamp"),
    "irrigation_water": ("water", "drain", "irrigation", "ec", "ph"),
    "setpoints": ("sp",),
    "radiation_energy": ("par", "radiation", "energy", "cost", "heat"),
    "outside_weather": ("outside", "wind", "rain"),
    "other_control_metadata": ("itemtype", "writetoi", "allow"),
}

# Intentionally conservative bounds. Review the variable definitions/units
# before interpreting any flagged value as an error.
BOUNDS = {
    "Rh": (0, 100),
    "OutsideRh": (0, 100),
    "Co2": (0, None),
    "Co2ViP": (0, None),
    "HumidityDeficity": (0, None),
    "HumidityDeficitViP": (0, None),
    "WindSpeed": (0, None),
    "Radiation": (0, None),
    "RadiationSum": (0, None),
    "Par": (0, None),
    "ParCumulative": (0, None),
    "ParOut": (0, None),
    "Rain": (0, 1),
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    raw = path.read_bytes()
    sample = raw[:65536].decode("utf-8-sig", errors="replace")
    try:
        sep = csv.Sniffer().sniff(sample, delimiters=",;\\t|").delimiter
    except csv.Error:
        sep = ","
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return (
                pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc, low_memory=False),
                enc,
                repr(sep),
            )
        except Exception as exc:
            last = exc
    raise ValueError(f"Unable to parse CSV: {last}")


def norm(value):
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


def parse_timestamp(series):
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed, "datetime/string"


def classify_column(column):
    name = norm(column)
    for group, hints in GROUP_RULES.items():
        if any(hint in name for hint in hints):
            return group
    return "unclassified"


def longest_missing_run(mask):
    """Return the longest consecutive run of True values."""
    longest = current = 0
    for value in mask:
        if value:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def add_title(lines, text):
    lines.extend(["", "=" * 96, text, "=" * 96, ""])


def audit(args):
    source = Path(args.input).expanduser().resolve()
    out = Path(args.output_dir).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(
            f"Input file not found: {source}\n"
            f"Current working directory: {Path.cwd()}\n"
            "Pass the correct path with --input, or resolve it relative to __file__."
        )
    if args.expected_minutes <= 0:
        raise ValueError("--expected-minutes must be positive")

    df, encoding, delimiter = read_csv(source)
    # Remove accidental whitespace around headers without changing source data.
    df.columns = [str(c).strip() for c in df.columns]
    time_col = next((c for c in df.columns if norm(c) == "timestamp"), None)
    if time_col is None:
        time_col = next(
            (
                c
                for c in df.columns
                if any(x in norm(c) for x in ("timestamp", "datetime", "ghtime"))
            ),
            None,
        )

    lines = [
        "CEAOD GREENHOUSE CUCUMBER — TIME-SERIES QUALITY AUDIT",
        "=" * 96,
        f"Dataset: {source}",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"File size: {source.stat().st_size:,} bytes",
        f"SHA-256: {sha256(source)}",
        f"Encoding: {encoding}",
        f"Delimiter: {delimiter}",
        f"Rows: {len(df):,}",
        f"Columns: {len(df.columns):,}",
        f"Memory usage: {df.memory_usage(deep=True).sum():,} bytes",
        f"Timestamp column: {time_col or 'NOT FOUND'}",
    ]

    # Parse timestamp once and use it throughout the audit.
    timestamps = None
    if time_col:
        timestamps = pd.to_datetime(df[time_col], errors="coerce")

    add_title(lines, "1. COLUMN INVENTORY AND VARIABLE GROUPS")
    for c in df.columns:
        lines.append(
            f"{c}: group={classify_column(c)}, dtype={df[c].dtype}, "
            f"non_null={df[c].notna().sum():,}, missing={df[c].isna().sum():,}, "
            f"unique={df[c].nunique(dropna=True):,}"
        )
    groups = {}
    for c in df.columns:
        groups.setdefault(classify_column(c), []).append(c)
    lines.append("\nColumns grouped by name (heuristic):")
    for group, cols in groups.items():
        lines.append(f"  {group}: {', '.join(cols)}")

    add_title(lines, "2. DATASET PREVIEW AND DESCRIPTIVE STATISTICS")
    lines.extend(
        [
            "FIRST 5 ROWS",
            df.head().to_string(index=False),
            "",
            "LAST 5 ROWS",
            df.tail().to_string(index=False),
            "",
            "DESCRIPTIVE STATISTICS (numeric and non-numeric)",
        ]
    )
    try:
        lines.append(df.describe(include="all").transpose().to_string())
    except Exception as exc:
        lines.append(f"Statistics unavailable: {exc}")

    add_title(lines, "3. MISSINGNESS PROFILE")
    missing_count = df.isna().sum()
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(missing_count.sum())
    lines.append(
        f"Missing cells: {missing_cells:,}/{total_cells:,} "
        f"({100 * missing_cells / total_cells if total_cells else 0:.4f}%)"
    )
    lines.append("\nColumns with missing values (sorted by missing percentage):")
    miss_rows = []
    for c in df.columns:
        count = int(missing_count[c])
        pct = 100 * count / max(len(df), 1)
        longest = longest_missing_run(df[c].isna().to_numpy())
        if count:
            lines.append(
                f"  {c}: {count:,} ({pct:.4f}%), longest consecutive run={longest:,}"
            )
        miss_rows.append(
            {
                "column": c,
                "missing": count,
                "missing_pct": pct,
                "non_missing": int(df[c].notna().sum()),
                "unique": int(df[c].nunique(dropna=True)),
                "longest_consecutive_missing_run": longest,
                "group": classify_column(c),
            }
        )
    all_missing = [c for c in df.columns if df[c].isna().all()]
    if all_missing:
        lines.append(f"\nEntirely missing columns: {all_missing}")
    else:
        lines.append("\nNo entirely missing columns.")
    if not missing_cells:
        lines.append("No missing values detected.")

    # Rows where all or most setpoint fields are missing can indicate a block
    # of unavailable controller metadata; report, do not interpret.
    setpoint_cols = [c for c in df.columns if norm(c).startswith("sp")]
    if setpoint_cols:
        row_missing = df[setpoint_cols].isna().sum(axis=1)
        lines.append(
            f"\nSetpoint fields: {len(setpoint_cols)}; "
            f"rows with all setpoints missing: {(row_missing == len(setpoint_cols)).sum():,}; "
            f"rows with at least one setpoint present: {(row_missing < len(setpoint_cols)).sum():,}"
        )

    add_title(lines, "4. TIMESTAMP VALIDITY, ORDER AND DUPLICATES")
    if timestamps is None:
        lines.append("Skipped: no timestamp column detected.")
    else:
        valid = timestamps.dropna()
        invalid = int((df[time_col].notna() & timestamps.isna()).sum())
        duplicate_mask = timestamps.notna() & timestamps.duplicated(keep=False)
        lines.extend(
            [
                f"Non-null source timestamps: {df[time_col].notna().sum():,}",
                f"Valid parsed timestamps: {len(valid):,}",
                f"Invalid non-null timestamps: {invalid:,}",
                f"Rows involved in duplicate timestamps: {int(duplicate_mask.sum()):,}",
                f"Distinct duplicated timestamp values: {timestamps[duplicate_mask].nunique():,}",
                f"First timestamp: {valid.min() if len(valid) else 'N/A'}",
                f"Last timestamp: {valid.max() if len(valid) else 'N/A'}",
                f"Rows out of chronological order: "
                f"{int((timestamps.diff().dropna() < pd.Timedelta(0)).sum()):,}",
            ]
        )

    add_title(
        lines, f"5. TEMPORAL COVERAGE AND {args.expected_minutes}-MINUTE INTERVALS"
    )
    if timestamps is None:
        lines.append("Skipped: no timestamp column detected.")
    else:
        valid_ts = timestamps.dropna()
        unique_ts = pd.DatetimeIndex(valid_ts.drop_duplicates().sort_values())
        if len(unique_ts) < 2:
            lines.append("Insufficient valid unique timestamps.")
        else:
            deltas = unique_ts.to_series().diff().dropna()
            step = pd.Timedelta(minutes=args.expected_minutes)
            mode = deltas.mode().iloc[0] if not deltas.mode().empty else pd.NaT
            lines.extend(
                [
                    f"Unique timestamps: {len(unique_ts):,}",
                    f"Most common interval: {mode}",
                    f"Intervals equal to expected step: {(deltas == step).sum():,}",
                    f"Intervals longer than expected: {(deltas > step).sum():,}",
                    f"Intervals shorter than expected: {(deltas < step).sum():,}",
                    f"Minimum observed interval: {deltas.min()}",
                    f"Maximum observed interval: {deltas.max()}",
                ]
            )
            expected = pd.date_range(unique_ts[0], unique_ts[-1], freq=step)
            absent = expected.difference(unique_ts)
            lines.extend(
                [
                    f"Expected timestamps at {args.expected_minutes}-minute cadence: {len(expected):,}",
                    f"Missing expected timestamps: {len(absent):,}",
                    f"Missing expected timestamp percentage: "
                    f"{100 * len(absent) / len(expected):.4f}%",
                ]
            )
            if len(absent):
                lines.append(f"First 20 missing timestamps: {list(absent[:20])}")
            if mode != step:
                lines.append(
                    "NOTE: observed modal interval differs from configured cadence; "
                    "the expected-grid result is a diagnostic, not a confirmed gap count."
                )

            # Daily coverage is calendar coverage only; the source is a high-frequency
            # time series, so it must not be described as daily production observations.
            dates = pd.DatetimeIndex(unique_ts.normalize().unique()).sort_values()
            expected_dates = pd.date_range(dates.min(), dates.max(), freq="D")
            missing_dates = expected_dates.difference(dates)
            lines.extend(
                [
                    f"\nCalendar dates represented: {len(dates):,}/{len(expected_dates):,}",
                    f"Calendar dates with no timestamp: {len(missing_dates):,}",
                ]
            )
            if len(missing_dates):
                lines.append(
                    f"Missing calendar dates: {[d.date() for d in missing_dates]}"
                )

    add_title(lines, "6. VARIABLE TYPES AND VALUE PROFILES")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    bool_like_cols = []
    categorical_cols = []
    for c in df.columns:
        vals = set(df[c].dropna().astype(str).str.strip().str.lower().unique())
        if vals and vals.issubset({"true", "false", "0", "1", "0.0", "1.0"}):
            bool_like_cols.append(c)
        elif c != time_col and (
            df[c].dtype == "object" or df[c].nunique(dropna=True) <= 20
        ):
            categorical_cols.append(c)
    lines.append(f"Numeric columns ({len(numeric_cols)}): {numeric_cols}")
    lines.append(f"Boolean-like columns ({len(bool_like_cols)}): {bool_like_cols}")
    lines.append(
        f"Categorical/low-cardinality candidates ({len(categorical_cols)}): {categorical_cols}"
    )
    for c in numeric_cols:
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        if not len(v):
            continue
        integer_ratio = float(
            np.isclose(
                v.to_numpy(dtype=float), np.round(v.to_numpy(dtype=float)), atol=1e-8
            ).mean()
        )
        lines.append(
            f"{c}: min={v.min():g}, max={v.max():g}, mean={v.mean():g}, "
            f"std={v.std():g}, unique={v.nunique():,}, "
            f"integer-like={100 * integer_ratio:.2f}%"
        )

    add_title(lines, "7. CONSERVATIVE DOMAIN SCREENING")
    checked = 0
    for c, (lower, upper) in BOUNDS.items():
        if c not in df.columns:
            continue
        values = pd.to_numeric(df[c], errors="coerce")
        present = values.notna()
        bad = pd.Series(False, index=df.index)
        if lower is not None:
            bad |= present & (values < lower)
        if upper is not None:
            bad |= present & (values > upper)
        count = int(bad.sum())
        checked += 1
        lines.append(
            f"{c}: checked={int(present.sum()):,}, outside broad bounds={count:,}, "
            f"bounds=[{lower}, {upper}]"
        )
        if count:
            lines.append(f"  Example row indices: {list(df.index[bad][:10])}")
    if not checked:
        lines.append("No named variables matched the configured screening rules.")
    lines.append(
        "\nThese bounds are only screening heuristics. Confirm units and definitions "
        "before classifying flagged observations as errors."
    )

    add_title(lines, "8. CONSTANT, INFINITE AND ZERO-VARIANCE COLUMNS")
    for c in numeric_cols:
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        if not len(v):
            lines.append(f"{c}: all values missing/non-numeric")
            continue
        if v.nunique() == 1:
            lines.append(f"{c}: constant value={v.iloc[0]!r}")
        if np.isinf(v.to_numpy(dtype=float)).any():
            lines.append(f"{c}: contains infinite values")
        if (v == 0).all():
            lines.append(f"{c}: all observed values are zero")

    add_title(lines, "9. AUDIT NOTES AND LIMITATIONS")
    lines.extend(
        [
            "- The dataset is treated as a high-frequency greenhouse time series, not a production table.",
            "- Variable groups are inferred from column names and need confirmation from documentation.",
            "- Missing values may mean unavailable, inactive, not applicable, or unrecorded; do not assume one meaning.",
            "- Consecutive missing-run length is measured in row order, not elapsed time.",
            "- Five-minute expected-grid gaps are calculated from the observed minimum to maximum timestamp.",
            "- Calendar-date coverage is not evidence of daily production observations.",
            "- Domain bounds are broad screening rules, not validated agronomic limits.",
            "- No causal, agronomic, or sensor-calibration conclusions are made.",
            "- The source CSV is never modified.",
        ]
    )

    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "ceaod_quality_audit.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    inventory = pd.DataFrame(
        {
            "column": df.columns,
            "group": [classify_column(c) for c in df.columns],
            "dtype": [str(df[c].dtype) for c in df.columns],
            "non_null": [int(df[c].notna().sum()) for c in df.columns],
            "missing": [int(df[c].isna().sum()) for c in df.columns],
            "missing_pct": [100 * df[c].isna().mean() for c in df.columns],
            "unique": [int(df[c].nunique(dropna=True)) for c in df.columns],
        }
    )
    inventory.to_csv(out / "ceaod_column_inventory.csv", index=False)
    pd.DataFrame(miss_rows).sort_values(
        ["missing_pct", "column"], ascending=[False, True]
    ).to_csv(out / "ceaod_missingness_profile.csv", index=False)
    if numeric_cols:
        df[numeric_cols].describe().T.to_csv(out / "ceaod_numeric_summary.csv")

    print("\n".join(lines))
    print(f"\nReport saved to: {report_path}")
    print(f"CSV summaries saved in: {out}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Audit the CEAOD greenhouse cucumber time series."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to source CSV")
    parser.add_argument(
        "--output-dir", default="reports/data_audit", help="Audit output directory"
    )
    parser.add_argument(
        "--expected-minutes",
        type=int,
        default=5,
        help="Expected sampling interval in minutes (default: 5)",
    )
    opts = parser.parse_args()
    try:
        raise SystemExit(audit(opts))
    except Exception as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

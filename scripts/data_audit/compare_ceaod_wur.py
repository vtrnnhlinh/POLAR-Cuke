#!/usr/bin/env python3
"""
Compare the CEAOD HiPower greenhouse time series against all timestamped CSVs
in the WUR Autonomous Greenhouse Challenge dataset.

What this script tests:
1. Timestamp-range and exact timestamp overlap.
2. Shared columns (case/punctuation-insensitive, with a small alias map).
3. Per-column value agreement at exactly matching timestamps.
4. Rows where every comparable shared field agrees.
5. Exact duplicates after canonicalizing common values.

Important:
- Timestamp overlap alone does NOT prove duplicate data.
- This script compares CEAOD against every timestamped WUR CSV, including
  each team's Greenhouse_climate.csv and vip.csv. Daily files are scanned too,
  but usually will not share a five-minute timestamp grid.
- It does not infer undocumented semantic equivalence between differently
  named variables. Extend ALIASES only after checking data dictionaries.
- WUR Excel serial timestamps are supported.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_CEAOD = "data/raw/GreenhouseCucumber/HiPower_NL_2018-08_2018-12.csv"
# Supply the actual directory containing the WUR team folders with --wur.

TIME_NAMES = {
    "timestamp",
    "datetime",
    "date_time",
    "time",
    "date",
    "ghtime",
    "measuredat",
    "recordedat",
    "measurementtime",
}

# Only syntactic/common abbreviations. Do not add semantic guesses without
# validating them against the WUR documentation.
ALIASES = {
    "temperature": "temp",
    "airtemperature": "temp",
    "relativehumidity": "rh",
    "humidity": "rh",
    "co2concentration": "co2",
    "carbon dioxide": "co2",
    "carbon dioxide concentration": "co2",
    "humiditydeficit": "humiditydeficit",
    "humiditydeficity": "humiditydeficit",  # CEAOD header spelling
}


def norm(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def canonical(name: object) -> str:
    key = norm(name)
    return ALIASES.get(key, key)


def read_csv(path: Path) -> pd.DataFrame:
    # Let pandas infer common encodings; WUR files are normally CSV.
    errors = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")
    raise ValueError("; ".join(errors))


def parse_timestamp(series: pd.Series) -> tuple[pd.Series, str]:
    """Parse text datetimes, Excel serial days, and Unix epoch timestamps."""
    numeric = pd.to_numeric(series, errors="coerce")
    non_null = series.notna()
    if non_null.any() and numeric[non_null].notna().mean() >= 0.95:
        med = float(numeric[non_null].median())
        if 20000 <= med <= 80000:
            parsed = pd.to_datetime(
                numeric, unit="D", origin="1899-12-30", errors="coerce"
            )
            # Excel serial-day floats can introduce sub-second rounding noise.
            return parsed.dt.round("s"), "Excel serial days (rounded to seconds)"
        if 1e8 <= med < 1e11:
            return pd.to_datetime(numeric, unit="s", errors="coerce"), "Unix seconds"
        if 1e11 <= med < 1e14:
            return (
                pd.to_datetime(numeric, unit="ms", errors="coerce"),
                "Unix milliseconds",
            )

    # format="mixed" is supported by pandas 2.x; fallback supports older pandas.
    try:
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    except (TypeError, ValueError):
        parsed = pd.to_datetime(series, errors="coerce")
    # Older pandas can parse format="mixed" as literal and return all NaT.
    if parsed.notna().sum() == 0 and non_null.any():
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed, "datetime/string"


def find_time_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if norm(col) in TIME_NAMES:
            return col
    # Secondary heuristic: a column with mostly parseable datetime values.
    for col in df.columns:
        sample = df[col].dropna().head(50)
        if len(sample) < 3:
            continue
        parsed, _ = parse_timestamp(sample)
        if parsed.notna().mean() >= 0.90:
            return col
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset(path: Path, label: str) -> dict:
    df = read_csv(path)
    source_row_count = len(df)
    df.columns = [str(c).strip() for c in df.columns]
    time_col = find_time_column(df)
    if time_col is None:
        raise ValueError(f"No timestamp-like column found in {path}")
    timestamps, time_format = parse_timestamp(df[time_col])
    df = df.copy()
    df["_audit_timestamp"] = timestamps
    df = df[df["_audit_timestamp"].notna()].copy()
    df = df.sort_values("_audit_timestamp")
    # Keep source duplicates visible in metadata, but de-duplicate for a
    # one-to-one timestamp merge. The first occurrence is retained.
    duplicate_count = int(df["_audit_timestamp"].duplicated(keep=False).sum())
    df = df.drop_duplicates("_audit_timestamp", keep="first")
    return {
        "label": label,
        "path": path,
        "df": df,
        "time_col": time_col,
        "time_format": time_format,
        "duplicate_timestamp_rows": duplicate_count,
        "rows_source": source_row_count,
        "rows_valid_unique": len(df),
        "sha256": sha256(path),
    }


def shared_column_pairs(
    left: pd.DataFrame, right: pd.DataFrame, left_time: str, right_time: str
) -> list[tuple[str, str, str]]:
    left_map = {}
    right_map = {}
    for c in left.columns:
        if c != "_audit_timestamp" and c != left_time:
            left_map.setdefault(canonical(c), c)
    for c in right.columns:
        if c != "_audit_timestamp" and c != right_time:
            right_map.setdefault(canonical(c), c)
    pairs = []
    for key in sorted(set(left_map) & set(right_map)):
        pairs.append((key, left_map[key], right_map[key]))
    return pairs


def compare_one(
    ceaod: dict, wur: dict, tolerance: float, min_shared: int
) -> tuple[dict, list[dict], list[dict]]:
    a = ceaod["df"]
    b = wur["df"]
    pairs = shared_column_pairs(a, b, ceaod["time_col"], wur["time_col"])

    # Rename shared columns before merging so identically named columns and
    # differently named aliases are both handled without ambiguous suffixes.
    left = a[["_audit_timestamp"]].copy()
    right = b[["_audit_timestamp"]].copy()
    for key, ca, cb in pairs:
        left[f"__ceaod_{key}"] = a[ca].to_numpy()
        right[f"__wur_{key}"] = b[cb].to_numpy()
    merged = left.merge(right, on="_audit_timestamp", how="inner")
    overlap_timestamps = len(merged)
    per_column = []
    match_masks = []

    for key, ca, cb in pairs:
        av = pd.to_numeric(merged[f"__ceaod_{key}"], errors="coerce")
        bv = pd.to_numeric(merged[f"__wur_{key}"], errors="coerce")
        both = av.notna() & bv.notna()
        compared = int(both.sum())
        if compared:
            diff = (av[both] - bv[both]).abs()
            exact = int((diff == 0).sum())
            within = int((diff <= tolerance).sum())
            max_diff = float(diff.max())
            mean_diff = float(diff.mean())
            agreement = within / compared
            equal = pd.Series(False, index=merged.index)
            equal.loc[both] = diff <= tolerance
            missingness_agrees = av.isna() == bv.isna()
            row_agreement = missingness_agrees & (~both | equal)
            match_masks.append((both, row_agreement))
        else:
            exact = within = 0
            max_diff = mean_diff = np.nan
            agreement = np.nan
            missingness_agrees = av.isna() == bv.isna()
            match_masks.append((both, missingness_agrees))

        per_column.append(
            {
                "wur_file": str(wur["path"]),
                "wur_team_or_file": wur["label"],
                "canonical_variable": key,
                "ceaod_column": ca,
                "wur_column": cb,
                "timestamps_overlapping": overlap_timestamps,
                "paired_non_missing_values": compared,
                "exact_equal_values": exact,
                "within_tolerance_values": within,
                "agreement_within_tolerance_pct": (
                    100 * agreement if pd.notna(agreement) else np.nan
                ),
                "mean_absolute_difference": mean_diff,
                "max_absolute_difference": max_diff,
            }
        )

    # A row is comparable when >= min_shared columns have non-null values
    # in both datasets. It is a full match when all such compared values agree.
    row_compared = np.zeros(overlap_timestamps, dtype=int)
    row_matched = np.ones(overlap_timestamps, dtype=bool)
    for both, row_agreement in match_masks:
        both_arr = both.to_numpy(dtype=bool)
        agreement_arr = row_agreement.to_numpy(dtype=bool)
        row_compared += both_arr.astype(int)
        row_matched &= agreement_arr

    eligible = row_compared >= min_shared
    full_match = (
        eligible & row_matched if pairs else np.zeros(overlap_timestamps, dtype=bool)
    )
    matched_rows = int(full_match.sum())
    candidate_pct = (
        100 * matched_rows / int(eligible.sum()) if eligible.any() else np.nan
    )

    row_records = []
    if overlap_timestamps:
        for idx in np.flatnonzero(full_match):
            row_records.append(
                {
                    "wur_file": str(wur["path"]),
                    "wur_team_or_file": wur["label"],
                    "timestamp": merged.iloc[idx]["_audit_timestamp"],
                    "shared_columns_compared": int(row_compared[idx]),
                    "match_type": "all_comparable_shared_values_within_tolerance",
                }
            )

    a_min = a["_audit_timestamp"].min() if len(a) else pd.NaT
    a_max = a["_audit_timestamp"].max() if len(a) else pd.NaT
    b_min = b["_audit_timestamp"].min() if len(b) else pd.NaT
    b_max = b["_audit_timestamp"].max() if len(b) else pd.NaT

    summary = {
        "wur_file": str(wur["path"]),
        "wur_team_or_file": wur["label"],
        "wur_rows": wur["rows_source"],
        "wur_valid_unique_timestamps": wur["rows_valid_unique"],
        "wur_duplicate_timestamp_rows": wur["duplicate_timestamp_rows"],
        "wur_timestamp_format": wur["time_format"],
        "wur_time_column": wur["time_col"],
        "wur_start": b_min,
        "wur_end": b_max,
        "ceaod_start": a_min,
        "ceaod_end": a_max,
        "timestamp_overlap_count": overlap_timestamps,
        "timestamp_overlap_pct_of_ceaod": (100 * overlap_timestamps / max(len(a), 1)),
        "shared_variable_count": len(pairs),
        "shared_variables": ";".join(x[0] for x in pairs),
        "eligible_rows_for_value_comparison": int(eligible.sum()),
        "full_matching_rows": matched_rows,
        "full_matching_rows_pct": candidate_pct,
        "value_tolerance": tolerance,
        "min_shared_variables_required": min_shared,
    }
    return summary, per_column, row_records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test record-level overlap between CEAOD and WUR greenhouse CSVs."
    )
    parser.add_argument("--ceaod", default=DEFAULT_CEAOD, help="CEAOD HiPower CSV path")
    parser.add_argument(
        "--wur",
        required=True,
        help="WUR dataset root directory containing team folders",
    )
    parser.add_argument("--output-dir", default="reports/ceaod_wur_comparison")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.0,
        help="Absolute numeric tolerance (default 0 = exact equality)",
    )
    parser.add_argument(
        "--min-shared",
        type=int,
        default=3,
        help="Minimum paired non-missing shared variables per matched row",
    )
    args = parser.parse_args()

    ceaod_path = Path(args.ceaod).expanduser().resolve()
    wur_root = Path(args.wur).expanduser().resolve()
    output = Path(args.output_dir).expanduser().resolve()

    if not ceaod_path.is_file():
        raise FileNotFoundError(f"CEAOD file not found: {ceaod_path}")
    if not wur_root.is_dir():
        raise NotADirectoryError(f"WUR directory not found: {wur_root}")
    if args.tolerance < 0 or args.min_shared < 1:
        raise ValueError("--tolerance must be >= 0 and --min-shared >= 1")

    print(f"Loading CEAOD: {ceaod_path}")
    ceaod = load_dataset(ceaod_path, "CEAOD")
    candidates = sorted(p for p in wur_root.rglob("*.csv") if p.resolve() != ceaod_path)
    print(f"Found {len(candidates)} WUR CSV files under {wur_root}")

    summaries, column_results, row_results, skipped = [], [], [], []
    for i, path in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] {path.relative_to(wur_root)}")
        try:
            wur = load_dataset(path, str(path.relative_to(wur_root)))
            summary, cols, rows = compare_one(
                ceaod, wur, args.tolerance, args.min_shared
            )
            summaries.append(summary)
            column_results.extend(cols)
            row_results.extend(rows)
        except Exception as exc:
            skipped.append({"wur_file": str(path), "reason": str(exc)})

    output.mkdir(parents=True, exist_ok=True)
    summary_df = pd.DataFrame(summaries)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(
            ["full_matching_rows", "timestamp_overlap_count", "shared_variable_count"],
            ascending=False,
        )
    summary_df.to_csv(output / "file_comparison.csv", index=False)
    pd.DataFrame(column_results).to_csv(output / "column_comparison.csv", index=False)
    pd.DataFrame(row_results).to_csv(output / "matching_records.csv", index=False)
    pd.DataFrame(skipped).to_csv(output / "skipped_files.csv", index=False)

    report = [
        "CEAOD vs WUR RECORD-OVERLAP INVESTIGATION",
        "=" * 88,
        f"CEAOD: {ceaod_path}",
        f"CEAOD SHA-256: {ceaod['sha256']}",
        f"CEAOD source rows: {ceaod['rows_source']:,}",
        f"CEAOD valid unique timestamps: {ceaod['rows_valid_unique']:,}",
        f"CEAOD timestamp column: {ceaod['time_col']}",
        f"CEAOD timestamp format: {ceaod['time_format']}",
        f"WUR root: {wur_root}",
        f"WUR CSV files discovered: {len(candidates)}",
        f"WUR CSV files compared: {len(summaries)}",
        f"WUR CSV files skipped: {len(skipped)}",
        f"Numeric tolerance: {args.tolerance}",
        f"Minimum shared variables per row: {args.min_shared}",
        "",
        "TOP CANDIDATE FILES (ranked by full matching rows, then timestamp overlap):",
    ]
    if summary_df.empty:
        report.append("No WUR files could be compared.")
    else:
        display_cols = [
            "wur_team_or_file",
            "timestamp_overlap_count",
            "shared_variable_count",
            "eligible_rows_for_value_comparison",
            "full_matching_rows",
            "full_matching_rows_pct",
            "shared_variables",
        ]
        report.append(summary_df[display_cols].head(20).to_string(index=False))
        report.extend(
            [
                "",
                "INTERPRETATION GUIDE:",
                "- Timestamp overlap only means both files contain observations at the same times.",
                "- Matching values across several shared variables at the same timestamps are much stronger evidence.",
                "- Full matching rows are counted only when at least --min-shared paired values exist",
                "  and every paired non-missing shared value agrees within --tolerance.",
                "- A zero-tolerance match is exact numeric equality after CSV parsing.",
                "- A high match rate in one WUR team/file is evidence of shared records, not by itself",
                "  proof of the precise publication/export lineage.",
                "- If no common columns are found, inspect column_comparison.csv and extend ALIASES",
                "  only after confirming that differently named variables are semantically equivalent.",
            ]
        )
    if skipped:
        report.extend(["", "SKIPPED FILES:"])
        report.extend(f"- {x['wur_file']}: {x['reason']}" for x in skipped)

    report_path = output / "comparison_report.txt"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nOutputs written to: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"COMPARISON FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

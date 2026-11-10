from pathlib import Path
from contextlib import redirect_stdout
import pandas as pd

ROOT = Path("data/raw/wur")
OUTPUT = Path("reports/data_audit/wur_value_inspection.txt")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def inspect_timestamp(folder, filename, column):
    path = folder / filename

    if not path.exists():
        print(f"\nMISSING FILE: {path}")
        return

    data = pd.read_csv(path)

    if column not in data.columns:
        print(f"\nMISSING COLUMN: {column} in {filename}")
        return

    values = data[column]

    print(f"\n{filename} — {column}")
    print(f"  Data type: {values.dtype}")
    print(f"  First values: {values.head(5).tolist()}")
    print(f"  Last values:  {values.tail(5).tolist()}")

    numeric = pd.to_numeric(values, errors="coerce")

    if numeric.notna().all():
        print(f"  Numeric range: {numeric.min()} to {numeric.max()}")

        # Excel serial date conversion
        dates = pd.to_datetime(
            numeric,
            unit="D",
            origin="1899-12-30"
        )

        print(f"  Possible date range: {dates.min()} to {dates.max()}")

    else:
        dates = pd.to_datetime(values, errors="coerce")
        if dates.notna().any():
            print(f"  Parsed date range: {dates.min()} to {dates.max()}")
        else:
            print("  Could not automatically parse timestamps.")


def inspect_production(folder):
    path = folder / "Production.csv"

    if not path.exists():
        print("\nProduction.csv not found.")
        return

    df = pd.read_csv(path)

    print("\nPRODUCTION")
    print("\nFirst 5 records:")
    print(df.head(5).to_string(index=False))

    print("\nLast 5 records:")
    print(df.tail(5).to_string(index=False))

    print("\nProduction statistics:")
    print(df.describe().to_string())

    print("\nPRODUCTION DIFFERENCES")
    for col in ["ProdA_cum", "ProdB_cum", "Total_Prod_cum"]:
        if col in df.columns:
            values = pd.to_numeric(df[col], errors="coerce")
            differences = values.diff()

            print(f"\n{col}:")
            print(differences.describe().to_string())
            print(f"Negative differences: {(differences < 0).sum()}")
            print(f"Missing differences: {differences.isna().sum()}")


with OUTPUT.open("w", encoding="utf-8") as report:
    with redirect_stdout(report):

        print("WUR DATASET — VALUE AND TIMESTAMP INSPECTION")
        print("=" * 80)
        print(f"Dataset directory: {ROOT}")
        print(f"Report generated: {pd.Timestamp.now()}")
        print("=" * 80)

        folders = sorted(p for p in ROOT.iterdir() if p.is_dir())

        for folder in folders:
            print("\n\n" + "=" * 80)
            print(f"TEAM: {folder.name}")
            print("=" * 80)

            inspect_production(folder)

            inspect_timestamp(
                folder, "Production.csv", "time"
            )

            inspect_timestamp(
                folder, "Greenhouse_climate.csv", "GHtime"
            )

            inspect_timestamp(
                folder, "Irrigation.csv", "time"
            )

print(f"Report successfully exported to: {OUTPUT}")

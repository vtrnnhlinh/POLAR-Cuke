from pathlib import Path

import pandas as pd

wur = Path("data/raw/wur")
ceaod_path = Path("data/raw/GreenhouseCucumber/HiPower_NL_2018-08_2018-12.csv")

# Load CEAOD
ceaod = pd.read_csv(ceaod_path)
ceaod["Timestamp"] = pd.to_datetime(ceaod["Timestamp"])


# Convert WUR Excel timestamps
def excel_to_datetime(series):
    return pd.to_datetime(series, unit="D", origin="1899-12-30").dt.round("s")


# Load WUR climate
climate = pd.read_csv(wur / "Sonoma" / "Greenhouse_climate.csv")

climate["Timestamp"] = excel_to_datetime(climate["GHtime"])

# Select overlapping period
start = ceaod["Timestamp"].min()
end = ceaod["Timestamp"].max()

climate = climate[climate["Timestamp"].between(start, end)].copy()

# Merge on exact timestamps
merged = ceaod.merge(climate, on="Timestamp", how="inner", suffixes=("_CEAOD", "_WUR"))

print(f"CEAOD period: {start} -> {end}")
print(f"CEAOD rows: {len(ceaod)}")
print(f"WUR rows in period: {len(climate)}")
print(f"Exact timestamp matches: {len(merged)}")

print("\nPaired measurements:")
pairs = [
    ("Temp", "Tair"),
    ("Rh", "RHair"),
    ("Co2", "CO2air"),
    ("HumidityDeficity", "HumDef"),
    ("VentLee_CEAOD", "VentLee_WUR"),
    ("VentWind", "Ventwind"),
]

columns = ["Timestamp"]

for a, b in pairs:
    if a in merged.columns and b in merged.columns:
        columns.extend([a, b])

print(merged[columns].head(20).to_string(index=False))

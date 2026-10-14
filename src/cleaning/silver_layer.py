import pandas as pd
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

input_file = PROJECT_ROOT / "data" / "processed" / "common_weather_data.csv"
output_dir = PROJECT_ROOT / "data" / "silver"

output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("SILVER LAYER PROCESSING")
print("=" * 60)

# Read Bronze/Common data
df = pd.read_csv(input_file)

print(f"Input records: {len(df)}")

# Remove completely empty rows
df = df.dropna(how="all")

# Remove duplicate records
df = df.drop_duplicates()

# Clean column names
df.columns = df.columns.str.strip()

# Convert date_time
if "date_time" in df.columns:
    df["date_time"] = pd.to_datetime(
        df["date_time"],
        errors="coerce"
    )

# Clean text columns
text_columns = [
    "city",
    "state",
    "event_type",
    "description",
    "source_type",
    "source_name",
    "verification_status"
]

for column in text_columns:
    if column in df.columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

# Convert numeric columns
numeric_columns = [
    "latitude",
    "longitude",
    "temperature",
    "rainfall",
    "humidity",
    "wind_speed"
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

# Add Silver layer metadata
df["silver_processing_time"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

df["silver_layer"] = "Silver"

# Output file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

output_file = output_dir / f"weather_silver_{timestamp}.csv"

df.to_csv(output_file, index=False)

print(f"Silver records: {len(df)}")
print(f"Output: {output_file}")

print("\nSource distribution:")
if "source_type" in df.columns:
    print(df["source_type"].value_counts())

print("\n" + "=" * 60)
print("SILVER LAYER CREATED SUCCESSFULLY")
print("=" * 60)
import pandas as pd
from pathlib import Path
from datetime import datetime


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Input file
INPUT_FILE = BASE_DIR / "data" / "processed" / "common_weather_data.csv"

# Bronze directory
BRONZE_DIR = BASE_DIR / "data" / "bronze"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)


def create_bronze_layer():

    print("===================================")
    print("BRONZE LAYER CREATION")
    print("===================================")

    # Check input file
    if not INPUT_FILE.exists():
        print("ERROR: Common schema file not found!")
        print(f"Expected file: {INPUT_FILE}")
        return

    print("Loading Common Weather Data...")

    # Read common schema
    df = pd.read_csv(INPUT_FILE)

    print(f"Records loaded: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Add ingestion metadata
    ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df["bronze_ingestion_time"] = ingestion_time
    df["bronze_layer"] = "Bronze"

    # Create timestamped Bronze file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = (
        BRONZE_DIR /
        f"weather_bronze_{timestamp}.csv"
    )

    # Save Bronze data
    df.to_csv(output_file, index=False)

    print()
    print("Bronze data saved:")
    print(output_file)

    print()
    print("===================================")
    print("BRONZE LAYER CREATED SUCCESSFULLY")
    print("===================================")

    print(f"Total Bronze records: {len(df)}")

    print()
    print("Records by source:")

    if "source_type" in df.columns:
        print(df["source_type"].value_counts())

    print()
    print("Bronze columns:")
    print(list(df.columns))


if __name__ == "__main__":
    create_bronze_layer()
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "datasets"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = RAW_DIR / "Sub_Division_IMD_2017.csv"


def load_dataset():
    print("Loading public rainfall dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


def clean_dataset(df):
    print("\nCleaning dataset...")

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove extra spaces from column names
    df.columns = df.columns.str.strip()

    # Convert YEAR to numeric
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    # Remove rows where YEAR is missing
    df = df.dropna(subset=["YEAR"])

    # Convert YEAR to integer
    df["YEAR"] = df["YEAR"].astype(int)

    return df


def save_processed_data(df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = (
        PROCESSED_DIR /
        f"rainfall_processed_{timestamp}.csv"
    )

    df.to_csv(output_file, index=False)

    print(f"\nProcessed dataset saved:")
    print(output_file)


def main():

    try:
        df = load_dataset()

        df = clean_dataset(df)

        save_processed_data(df)

        print("\n===================================")
        print("DATASET INGESTION COMPLETED")
        print("===================================")

        print(f"\nFinal records: {len(df)}")

        print("\nColumns:")
        print(list(df.columns))

        print("\nFirst 5 records:")
        print(df.head().to_string(index=False))

    except FileNotFoundError:
        print("\nERROR: Dataset file not found.")
        print(f"Expected file: {INPUT_FILE}")

    except Exception as error:
        print(f"\nPipeline failed: {error}")


if __name__ == "__main__":
    main()
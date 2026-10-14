from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "social_media"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = RAW_DIR / "train.csv"


def load_data():
    print("Loading social media dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    return df


def clean_data(df):
    print("\nCleaning social media data...")

    # Clean column names
    df.columns = df.columns.str.strip()

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate tweet IDs
    df = df.drop_duplicates(subset=["id"])

    # Fill missing text/location/keyword values
    df["text"] = df["text"].fillna("")
    df["location"] = df["location"].fillna("Unknown")
    df["keyword"] = df["keyword"].fillna("Unknown")

    # Convert target to integer
    df["target"] = pd.to_numeric(
        df["target"],
        errors="coerce"
    )

    print(f"Rows after cleaning: {len(df)}")

    return df


def add_project_columns(df):
    print("\nAdding project metadata...")

    df["source_type"] = "Social Media"
    df["source_name"] = "Kaggle Disaster Tweets"
    df["ingestion_time"] = datetime.now().isoformat()
    df["verification_status"] = "Pending"

    return df


def save_processed_data(df):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = (
        PROCESSED_DIR /
        f"social_media_processed_{timestamp}.csv"
    )

    df.to_csv(output_file, index=False)

    print(f"\nProcessed data saved:")
    print(output_file)


def main():

    try:
        df = load_data()

        df = clean_data(df)

        df = add_project_columns(df)

        save_processed_data(df)

        print("\n===================================")
        print("SOCIAL MEDIA INGESTION COMPLETED")
        print("===================================")

        print(f"\nFinal records: {len(df)}")

        print("\nColumns:")
        print(list(df.columns))

        print("\nTarget distribution:")
        print(df["target"].value_counts().to_string())

        print("\nSample records:")
        print(df.head().to_string(index=False))

    except FileNotFoundError:
        print("\nERROR: train.csv not found.")
        print(f"Expected location: {INPUT_FILE}")

    except Exception as error:
        print(f"\nPipeline failed: {error}")


if __name__ == "__main__":
    main()
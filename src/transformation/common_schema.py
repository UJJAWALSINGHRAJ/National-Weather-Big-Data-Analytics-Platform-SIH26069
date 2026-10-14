from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CITIZEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "citizen_reports"
    / "citizen_reports.csv"
)

OUTPUT_FILE = PROCESSED_DIR / "common_weather_data.csv"

COMMON_COLUMNS = [
    "report_id",
    "source_type",
    "source_name",
    "date_time",
    "city",
    "state",
    "latitude",
    "longitude",
    "event_type",
    "description",
    "temperature",
    "rainfall",
    "humidity",
    "wind_speed",
    "media_url",
    "verification_status",
    "created_at"
]


def empty_common_dataframe():
    return pd.DataFrame(columns=COMMON_COLUMNS)


def load_latest_file(pattern):
    files = sorted(PROCESSED_DIR.glob(pattern))

    if not files:
        return None

    return pd.read_csv(files[-1])


def transform_api():
    df = load_latest_file("weather_processed_*.csv")

    if df is None:
        print("API processed file not found.")
        return empty_common_dataframe()

    result = pd.DataFrame()

    result["report_id"] = df["report_id"]
    result["source_type"] = df["source_type"]
    result["source_name"] = df["source_name"]
    result["date_time"] = df["date_time"]
    result["city"] = df["city"]
    result["state"] = df["state"]
    result["latitude"] = df["latitude"]
    result["longitude"] = df["longitude"]
    result["event_type"] = "Weather Observation"
    result["description"] = ""
    result["temperature"] = df["temperature_c"]
    result["rainfall"] = df["precipitation_mm"]
    result["humidity"] = df["humidity_percent"]
    result["wind_speed"] = df["wind_speed_kmh"]
    result["media_url"] = ""
    result["verification_status"] = df["verification_status"]
    result["created_at"] = df["ingestion_time"]

    return result[COMMON_COLUMNS]


def transform_social_media():
    df = load_latest_file("social_media_processed_*.csv")

    if df is None:
        print("Social media processed file not found.")
        return empty_common_dataframe()

    result = pd.DataFrame()

    result["report_id"] = df["id"].astype(str)
    result["source_type"] = df["source_type"]
    result["source_name"] = df["source_name"]
    result["date_time"] = ""
    result["city"] = df["location"]
    result["state"] = ""
    result["latitude"] = None
    result["longitude"] = None
    result["event_type"] = "Unclassified"
    result["description"] = df["text"]
    result["temperature"] = None
    result["rainfall"] = None
    result["humidity"] = None
    result["wind_speed"] = None
    result["media_url"] = ""
    result["verification_status"] = df["verification_status"]
    result["created_at"] = df["ingestion_time"]

    return result[COMMON_COLUMNS]


def transform_citizen_reports():
    if not CITIZEN_FILE.exists():
        print("Citizen report file not found.")
        return empty_common_dataframe()

    df = pd.read_csv(CITIZEN_FILE)

    result = pd.DataFrame()

    result["report_id"] = df["report_id"]
    result["source_type"] = df["source_type"]
    result["source_name"] = df["source_name"]
    result["date_time"] = df["date_time"]
    result["city"] = df["city"]
    result["state"] = df["state"]
    result["latitude"] = df["latitude"]
    result["longitude"] = df["longitude"]
    result["event_type"] = df["event_type"]
    result["description"] = df["description"]
    result["temperature"] = None
    result["rainfall"] = None
    result["humidity"] = None
    result["wind_speed"] = None
    result["media_url"] = df["media_url"]
    result["verification_status"] = df["verification_status"]
    result["created_at"] = df["created_at"]

    return result[COMMON_COLUMNS]


def transform_dataset():
    df = load_latest_file("rainfall_processed_*.csv")

    if df is None:
        print("Rainfall dataset processed file not found.")
        return empty_common_dataframe()

    rows = []

    for _, row in df.iterrows():

        year = int(row["YEAR"])

        rows.append({
            "report_id": f"RAINFALL-{year}-{row['SUBDIVISION']}",
            "source_type": "Public Dataset",
            "source_name": "IMD Rainfall Dataset",
            "date_time": f"{year}-12-31",
            "city": "",
            "state": row["SUBDIVISION"],
            "latitude": None,
            "longitude": None,
            "event_type": "Rainfall",
            "description": (
                f"Annual rainfall record for "
                f"{row['SUBDIVISION']} in {year}."
            ),
            "temperature": None,
            "rainfall": row["ANNUAL"],
            "humidity": None,
            "wind_speed": None,
            "media_url": "",
            "verification_status": "Dataset Record",
            "created_at": ""
        })

    return pd.DataFrame(rows, columns=COMMON_COLUMNS)


def transform_website():
    files = sorted(
        PROCESSED_DIR.glob("imd_website_processed_*.txt")
    )

    if not files:
        print("Website processed file not found.")
        return empty_common_dataframe()

    latest_file = files[-1]

    with open(latest_file, "r", encoding="utf-8") as file:
        text = file.read()

    result = pd.DataFrame([{
        "report_id": "WEB-" + latest_file.stem.split("_")[-2]
        + latest_file.stem.split("_")[-1],
        "source_type": "Website",
        "source_name": "India Meteorological Department",
        "date_time": "",
        "city": "",
        "state": "",
        "latitude": None,
        "longitude": None,
        "event_type": "Rainfall Information",
        "description": text,
        "temperature": None,
        "rainfall": None,
        "humidity": None,
        "wind_speed": None,
        "media_url": "",
        "verification_status": "Pending",
        "created_at": ""
    }])

    return result[COMMON_COLUMNS]


def main():

    print("===================================")
    print("COMMON SCHEMA TRANSFORMATION")
    print("===================================\n")

    print("Transforming API data...")
    api_data = transform_api()
    print(f"API records: {len(api_data)}")

    print("\nTransforming Public Dataset...")
    dataset_data = transform_dataset()
    print(f"Dataset records: {len(dataset_data)}")

    print("\nTransforming Social Media data...")
    social_data = transform_social_media()
    print(f"Social Media records: {len(social_data)}")

    print("\nTransforming Citizen Reports...")
    citizen_data = transform_citizen_reports()
    print(f"Citizen Report records: {len(citizen_data)}")

    print("\nTransforming Website data...")
    website_data = transform_website()
    print(f"Website records: {len(website_data)}")

    final_data = pd.concat(
        [
            api_data,
            dataset_data,
            social_data,
            citizen_data,
            website_data
        ],
        ignore_index=True
    )

    final_data = final_data[COMMON_COLUMNS]

    final_data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n===================================")
    print("COMMON SCHEMA CREATED SUCCESSFULLY")
    print("===================================")

    print(f"\nTotal records: {len(final_data)}")
    print(f"Output file: {OUTPUT_FILE}")

    print("\nRecords by source:")
    print(
        final_data["source_type"]
        .value_counts()
        .to_string()
    )

    print("\nCommon columns:")
    print(COMMON_COLUMNS)


if __name__ == "__main__":
    main()
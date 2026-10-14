import json
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "api"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


API_URL = "https://api.open-meteo.com/v1/forecast"

LATITUDE = 26.2389
LONGITUDE = 73.0243

PARAMETERS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "timezone": "Asia/Kolkata",
    "current": (
        "temperature_2m,"
        "relative_humidity_2m,"
        "precipitation,"
        "rain,"
        "weather_code,"
        "wind_speed_10m"
    )
}


def fetch_weather_data():
    print("Fetching weather data...")

    response = requests.get(
        API_URL,
        params=PARAMETERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_data(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = RAW_DIR / f"weather_{timestamp}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print(f"Raw data saved: {file_path}")


def create_dataframe(data):

    current = data["current"]

    row = {
        "report_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "source_type": "API",
        "source_name": "Open-Meteo",
        "date_time": current["time"],
        "city": "Jodhpur",
        "state": "Rajasthan",
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "temperature_c": current["temperature_2m"],
        "humidity_percent": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "rain_mm": current["rain"],
        "weather_code": current["weather_code"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "verification_status": "Pending",
        "ingestion_time": datetime.now().isoformat()
    }

    return pd.DataFrame([row])


def save_processed_data(df):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = (
        PROCESSED_DIR /
        f"weather_processed_{timestamp}.csv"
    )

    df.to_csv(file_path, index=False)

    print(f"Processed data saved: {file_path}")


def main():

    try:

        data = fetch_weather_data()

        save_raw_data(data)

        df = create_dataframe(data)

        save_processed_data(df)

        print("\n===================================")
        print("API INGESTION COMPLETED SUCCESSFULLY")
        print("===================================")

        print(f"\nRecords created: {len(df)}")

        print("\nCollected Data:")
        print(df.to_string(index=False))

    except requests.exceptions.RequestException as error:

        print(f"API request failed: {error}")

    except Exception as error:

        print(f"Pipeline failed: {error}")


if __name__ == "__main__":
    main()
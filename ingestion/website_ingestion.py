from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "websites"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

WEBSITE_URL = "https://mausam.imd.gov.in/responsive/rainfallinformation.php"


def fetch_website():
    print("Connecting to IMD website...")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        WEBSITE_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def save_raw_html(html):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = RAW_DIR / f"imd_rainfall_{timestamp}.html"

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html)

    print(f"Raw website data saved: {file_path}")


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove unnecessary elements
    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return text


def save_processed_data(text):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = (
        PROCESSED_DIR /
        f"imd_website_processed_{timestamp}.txt"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("SOURCE_TYPE: Website\n")
        file.write("SOURCE_NAME: India Meteorological Department\n")
        file.write(f"SOURCE_URL: {WEBSITE_URL}\n")
        file.write(f"INGESTION_TIME: {datetime.now().isoformat()}\n\n")
        file.write(text)

    print(f"Processed website data saved: {file_path}")


def main():

    try:
        html = fetch_website()

        save_raw_html(html)

        text = extract_text(html)

        save_processed_data(text)

        print("\n===================================")
        print("WEBSITE INGESTION COMPLETED")
        print("===================================")

        print(f"\nExtracted characters: {len(text)}")

    except requests.exceptions.RequestException as error:
        print(f"\nWebsite request failed: {error}")

    except Exception as error:
        print(f"\nPipeline failed: {error}")


if __name__ == "__main__":
    main()
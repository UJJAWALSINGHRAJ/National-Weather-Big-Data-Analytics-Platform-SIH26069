import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "citizen_reports"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "citizen_reports.csv"


st.set_page_config(
    page_title="Citizen Weather Report",
    page_icon="🌦️",
    layout="centered"
)

st.title("🌦️ Citizen Weather & Disaster Report")
st.write(
    "Submit a weather or disaster report. "
    "All submitted reports will be marked as Pending "
    "until verified by the Admin."
)

with st.form("citizen_report_form"):

    st.subheader("Report Details")

    city = st.text_input("City")

    state = st.text_input("State")

    event_type = st.selectbox(
        "Event Type",
        [
            "Heavy Rain",
            "Thunderstorm",
            "Flooding",
            "Heatwave",
            "Fog",
            "Dust Storm",
            "Strong Wind",
            "Other"
        ]
    )

    description = st.text_area(
        "Describe the Weather / Disaster Event"
    )

    latitude = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=0.0
    )

    longitude = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=0.0
    )

    photo = st.file_uploader(
        "Upload Photo / Video (Optional)",
        type=["jpg", "jpeg", "png", "mp4"]
    )

    submitted = st.form_submit_button(
        "Submit Report"
    )


if submitted:

    if not city or not state or not description:

        st.error(
            "Please fill City, State and Description."
        )

    else:

        report_id = "CR-" + uuid.uuid4().hex[:8].upper()

        report_time = datetime.now().isoformat()

        media_name = ""

        if photo is not None:

            media_dir = RAW_DIR / "media"
            media_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            media_path = media_dir / photo.name

            with open(media_path, "wb") as file:
                file.write(photo.getbuffer())

            media_name = photo.name

        new_report = pd.DataFrame([{
            "report_id": report_id,
            "source_type": "Citizen Report",
            "source_name": "Citizen Reporting Portal",
            "date_time": report_time,
            "city": city,
            "state": state,
            "latitude": latitude,
            "longitude": longitude,
            "event_type": event_type,
            "description": description,
            "media_url": media_name,
            "verification_status": "Pending",
            "created_at": report_time
        }])

        if OUTPUT_FILE.exists():

            existing_data = pd.read_csv(
                OUTPUT_FILE
            )

            updated_data = pd.concat(
                [existing_data, new_report],
                ignore_index=True
            )

        else:

            updated_data = new_report

        updated_data.to_csv(
            OUTPUT_FILE,
            index=False
        )

        st.success(
            f"Report submitted successfully! "
            f"Report ID: {report_id}"
        )

        st.info(
            "Verification Status: Pending"
        )

import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# NATIONAL WEATHER BIG DATA ANALYTICS PLATFORM
# GOLD LAYER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Latest Silver file
silver_dir = PROJECT_ROOT / "data" / "silver"
gold_dir = PROJECT_ROOT / "data" / "gold"

gold_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("GOLD LAYER PROCESSING")
print("=" * 60)

# ------------------------------------------------------------
# 1. Find latest Silver file
# ------------------------------------------------------------

silver_files = list(silver_dir.glob("weather_silver_*.csv"))

if not silver_files:
    print("❌ No Silver layer file found.")
    raise FileNotFoundError("Silver layer file not found.")

latest_silver = max(silver_files, key=lambda x: x.stat().st_mtime)

print(f"Reading Silver file: {latest_silver}")

df = pd.read_csv(latest_silver)

print(f"Silver records loaded: {len(df)}")

# ------------------------------------------------------------
# 2. Basic cleaning
# ------------------------------------------------------------

df.columns = df.columns.str.strip()

# Clean event type
if "event_type" in df.columns:
    df["event_type"] = (
        df["event_type"]
        .fillna("Unclassified")
        .astype(str)
        .str.strip()
    )

    df.loc[
        df["event_type"].isin(["", "nan", "None"]),
        "event_type"
    ] = "Unclassified"

# Clean source type
if "source_type" in df.columns:
    df["source_type"] = (
        df["source_type"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

# ------------------------------------------------------------
# 3. EVENT ANALYTICS
# ------------------------------------------------------------

print("\nCreating Event Analytics...")

event_analytics = (
    df.groupby("event_type")
      .size()
      .reset_index(name="report_count")
      .sort_values("report_count", ascending=False)
)

event_analytics["analysis_time"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

event_file = gold_dir / "event_analytics.csv"

event_analytics.to_csv(
    event_file,
    index=False
)

print(f"Event analytics saved: {event_file}")

# ------------------------------------------------------------
# 4. SOURCE ANALYTICS
# ------------------------------------------------------------

print("\nCreating Source Analytics...")

source_analytics = (
    df.groupby("source_type")
      .size()
      .reset_index(name="report_count")
      .sort_values("report_count", ascending=False)
)

source_analytics["analysis_time"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

source_file = gold_dir / "source_analytics.csv"

source_analytics.to_csv(
    source_file,
    index=False
)

print(f"Source analytics saved: {source_file}")

# ------------------------------------------------------------
# 5. STATE-WISE RAINFALL
# ------------------------------------------------------------

print("\nCreating State-wise Rainfall Analytics...")

if "state" in df.columns and "rainfall" in df.columns:

    rainfall_df = df.copy()

    rainfall_df["rainfall"] = pd.to_numeric(
        rainfall_df["rainfall"],
        errors="coerce"
    )

    state_rainfall = (
        rainfall_df
        .dropna(subset=["state"])
        .groupby("state")
        .agg(
            total_rainfall=("rainfall", "sum"),
            average_rainfall=("rainfall", "mean"),
            report_count=("report_id", "count")
        )
        .reset_index()
        .sort_values(
            "total_rainfall",
            ascending=False
        )
    )

else:

    state_rainfall = pd.DataFrame(
        columns=[
            "state",
            "total_rainfall",
            "average_rainfall",
            "report_count"
        ]
    )

state_rainfall["analysis_time"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)

state_file = gold_dir / "state_rainfall.csv"

state_rainfall.to_csv(
    state_file,
    index=False
)

print(f"State rainfall saved: {state_file}")

# ------------------------------------------------------------
# 6. WEATHER SUMMARY
# ------------------------------------------------------------

print("\nCreating Weather Summary...")

summary = {
    "total_reports": len(df),
    "total_sources": df["source_type"].nunique()
        if "source_type" in df.columns else 0,
    "total_event_types": df["event_type"].nunique()
        if "event_type" in df.columns else 0,
    "processing_time": datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
}

weather_summary = pd.DataFrame([summary])

summary_file = gold_dir / "weather_summary.csv"

weather_summary.to_csv(
    summary_file,
    index=False
)

print(f"Weather summary saved: {summary_file}")

# ------------------------------------------------------------
# 7. DISPLAY RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("GOLD LAYER SUMMARY")
print("=" * 60)

print(f"Total Reports: {len(df)}")

print("\nReports by Source:")
print(source_analytics)

print("\nReports by Event:")
print(event_analytics)

print("\nState-wise Rainfall:")
print(state_rainfall.head(10))

print("\n" + "=" * 60)
print("✅ GOLD LAYER CREATED SUCCESSFULLY")
print("=" * 60)
import subprocess
import sys


def run_step(name, script):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n❌ {name} FAILED")
        sys.exit(1)

    print(f"\n✅ {name} COMPLETED")


steps = [
    ("API INGESTION", "ingestion/api_ingestion.py"),
    ("PUBLIC DATASET INGESTION", "ingestion/dataset_ingestion.py"),
    ("WEBSITE INGESTION", "ingestion/website_ingestion.py"),
    ("SOCIAL MEDIA INGESTION", "ingestion/social_media_ingestion.py"),
    ("CITIZEN REPORT INGESTION", "ingestion/citizen_report_ingestion.py"),
    ("COMMON SCHEMA TRANSFORMATION", "src/transformation/common_schema.py"),
    ("BRONZE LAYER CREATION", "src/cleaning/bronze_layer.py"),
    ("SILVER LAYER CREATION", "src/cleaning/silver_layer.py"),
    ("GOLD LAYER CREATION", "src/analytics/gold_layer.py"),
    ("AI/ML CLASSIFICATION", "src/ml/weather_ml.py")
]


print("\n" + "=" * 60)
print("NATIONAL WEATHER DATA PIPELINE")
print("=" * 60)

for name, script in steps:
    run_step(name, script)

print("\n" + "=" * 60)
print("🎉 END-TO-END PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)
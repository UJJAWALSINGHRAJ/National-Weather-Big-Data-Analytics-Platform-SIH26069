# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.ml import Pipeline
from pyspark.ml.feature import Tokenizer, HashingTF, IDF, StringIndexer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

BASE_PATH = "abfss://weather-data@sihstorage1.dfs.core.windows.net"

BRONZE_PATH = f"{BASE_PATH}/bronze/"
SILVER_PATH = f"{BASE_PATH}/silver/"
GOLD_PATH = f"{BASE_PATH}/gold/"

print("Configuration loaded successfully")
print("BASE PATH:", BASE_PATH)

# COMMAND ----------

print("===== BRONZE =====")
display(dbutils.fs.ls(BRONZE_PATH))

print("===== SILVER =====")
display(dbutils.fs.ls(SILVER_PATH))

print("===== GOLD =====")
display(dbutils.fs.ls(GOLD_PATH))

# COMMAND ----------

bronze_files = [
    f.path
    for f in dbutils.fs.ls(BRONZE_PATH)
    if f.name.startswith("weather_bronze_") and f.name.endswith(".csv")
]

if not bronze_files:
    raise Exception("No weather_bronze_*.csv file found")

bronze_file = sorted(bronze_files)[-1]

print("Latest Bronze file:")
print(bronze_file)

# COMMAND ----------

bronze_df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .csv(bronze_file)
)

print("Bronze records:", bronze_df.count())
display(bronze_df.limit(10))

# COMMAND ----------

print("===== BRONZE SOURCE COUNTS =====")

display(
    bronze_df
    .groupBy("source_type")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

silver_df = bronze_df

# Remove records without report_id
silver_df = silver_df.filter(
    F.col("report_id").isNotNull() &
    (F.trim(F.col("report_id")) != "")
)

# Clean text columns
text_columns = [
    "report_id",
    "source_type",
    "source_name",
    "city",
    "state",
    "event_type",
    "description",
    "media_url",
    "verification_status"
]

for col_name in text_columns:
    if col_name in silver_df.columns:
        silver_df = silver_df.withColumn(
            col_name,
            F.trim(F.col(col_name))
        )

# Remove duplicate reports
silver_df = silver_df.dropDuplicates(["report_id"])

# Add Silver metadata
silver_df = (
    silver_df
    .withColumn("silver_processing_time", F.current_timestamp())
    .withColumn("silver_layer", F.lit("Silver"))
)

print("Bronze records:", bronze_df.count())
print("Silver records:", silver_df.count())

# COMMAND ----------

print("===== SILVER VALIDATION =====")

null_report_ids = silver_df.filter(
    F.col("report_id").isNull()
).count()

duplicate_report_ids = (
    silver_df
    .groupBy("report_id")
    .count()
    .filter(F.col("count") > 1)
    .count()
)

print("Silver records:", silver_df.count())
print("Null report IDs:", null_report_ids)
print("Duplicate report IDs:", duplicate_report_ids)

print("\n===== SOURCE COUNTS =====")

display(
    silver_df
    .groupBy("source_type")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

silver_output = f"{SILVER_PATH}weather_silver_latest/"

silver_df.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(silver_output)

print("Silver layer saved successfully")
print("Path:", silver_output)

# COMMAND ----------

silver_gold = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "false")
    .csv(silver_output)
)

# Safe numeric conversion
numeric_columns = [
    "latitude",
    "longitude",
    "temperature",
    "rainfall",
    "humidity",
    "wind_speed"
]

for col_name in numeric_columns:
    if col_name in silver_gold.columns:
        silver_gold = silver_gold.withColumn(
            col_name,
            F.expr(f"try_cast({col_name} AS DOUBLE)")
        )

print("Silver records loaded:", silver_gold.count())

# COMMAND ----------

gold_ready_df = silver_gold.filter(
    F.col("event_type").isNotNull() &
    (F.trim(F.col("event_type")) != "") &
    (~F.col("event_type").rlike(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    ))
)

print("Silver records:", silver_gold.count())
print("Gold-ready records:", gold_ready_df.count())

# COMMAND ----------

gold_event = (
    gold_ready_df
    .groupBy("event_type")
    .agg(
        F.count("*").alias("total_reports"),
        F.countDistinct("state").alias("states_affected"),
        F.avg("rainfall").alias("avg_rainfall"),
        F.avg("temperature").alias("avg_temperature"),
        F.avg("humidity").alias("avg_humidity"),
        F.avg("wind_speed").alias("avg_wind_speed")
    )
    .orderBy(F.desc("total_reports"))
)

display(gold_event)

# COMMAND ----------

gold_event_path = f"{GOLD_PATH}event_analytics/"

gold_event.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(gold_event_path)

print("Event analytics saved")

# COMMAND ----------

valid_sources = [
    "Social Media",
    "Public Dataset",
    "API",
    "Citizen Report",
    "Website"
]

gold_source = (
    gold_ready_df
    .filter(F.col("source_type").isin(valid_sources))
    .groupBy("source_type")
    .agg(
        F.count("*").alias("total_reports"),
        F.countDistinct("state").alias("states_covered")
    )
    .orderBy(F.desc("total_reports"))
)

display(gold_source)

# COMMAND ----------

gold_source_path = f"{GOLD_PATH}source_analytics/"

gold_source.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(gold_source_path)

print("Source analytics saved")

# COMMAND ----------

gold_state = (
    gold_ready_df
    .filter(F.col("source_type") == "Public Dataset")
    .groupBy("state")
    .agg(
        F.count("*").alias("total_reports"),
        F.avg("rainfall").alias("avg_rainfall")
    )
    .orderBy(F.desc("avg_rainfall"))
)

display(gold_state)

# COMMAND ----------

gold_state_path = f"{GOLD_PATH}state_rainfall/"

gold_state.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(gold_state_path)

print("State rainfall analytics saved")

# COMMAND ----------

social_df = (
    gold_ready_df
    .filter(F.col("source_type") == "Social Media")
)

print("Social Media records:", social_df.count())

display(
    social_df
    .select(
        "report_id",
        "description",
        "source_type",
        "verification_status"
    )
    .limit(10)
)

# COMMAND ----------

ml_df = (
    social_df
    .select(
        "report_id",
        "description",
        "verification_status"
    )
    .withColumn(
        "clean_text",
        F.lower(
            F.regexp_replace(
                F.coalesce(F.col("description"), F.lit("")),
                r"http\S+|www\S+",
                ""
            )
        )
    )
    .withColumn(
        "clean_text",
        F.regexp_replace(
            F.col("clean_text"),
            r"[^a-zA-Z\s]",
            " "
        )
    )
    .withColumn(
        "clean_text",
        F.regexp_replace(
            F.col("clean_text"),
            r"\s+",
            " "
        )
    )
    .withColumn(
        "clean_text",
        F.trim(F.col("clean_text"))
    )
)

print("Total Social Media records:", ml_df.count())

# COMMAND ----------

ml_labeled_df = (
    ml_df
    .withColumn(
        "event_category",
        F.when(
            F.col("clean_text").rlike(
                r"\b(rain|rainfall|raining|downpour|storm rain)\b"
            ),
            "Rainfall"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(thunder|thunderstorm|lightning)\b"
            ),
            "Thunderstorm"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(flood|flooding|flooded)\b"
            ),
            "Flooding"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(heatwave|heat wave|extreme heat)\b"
            ),
            "Heatwave"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(fog|foggy)\b"
            ),
            "Fog"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(dust storm|duststorm)\b"
            ),
            "Dust Storm"
        )
        .when(
            F.col("clean_text").rlike(
                r"\b(wind|winds|strong wind|high wind)\b"
            ),
            "Strong Wind"
        )
        .otherwise("Other")
    )
)

print("===== EVENT LABEL DISTRIBUTION =====")

display(
    ml_labeled_df
    .groupBy("event_category")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

ml_training_df = (
    ml_labeled_df
    .filter(
        F.col("clean_text").isNotNull() &
        (F.trim(F.col("clean_text")) != "")
    )
    .select(
        "report_id",
        "clean_text",
        "event_category"
    )
)

print("Usable ML records:", ml_training_df.count())

# COMMAND ----------

train_df, test_df = ml_training_df.randomSplit(
    [0.8, 0.2],
    seed=42
)

print("Train records:", train_df.count())
print("Test records:", test_df.count())

# COMMAND ----------

label_indexer = StringIndexer(
    inputCol="event_category",
    outputCol="label",
    handleInvalid="keep"
)

tokenizer = Tokenizer(
    inputCol="clean_text",
    outputCol="words"
)

hashing_tf = HashingTF(
    inputCol="words",
    outputCol="rawFeatures",
    numFeatures=10000
)

idf = IDF(
    inputCol="rawFeatures",
    outputCol="features"
)

classifier = LogisticRegression(
    featuresCol="features",
    labelCol="label",
    maxIter=20
)

ml_pipeline = Pipeline(
    stages=[
        label_indexer,
        tokenizer,
        hashing_tf,
        idf,
        classifier
    ]
)

print("ML pipeline created successfully")

# COMMAND ----------

evaluation_model = ml_pipeline.fit(train_df)

test_predictions = evaluation_model.transform(test_df)

print("Test predictions:", test_predictions.count())

# COMMAND ----------

accuracy_evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="accuracy"
)

precision_evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="weightedPrecision"
)

recall_evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="weightedRecall"
)

f1_evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="f1"
)

accuracy = accuracy_evaluator.evaluate(test_predictions)
precision = precision_evaluator.evaluate(test_predictions)
recall = recall_evaluator.evaluate(test_predictions)
f1 = f1_evaluator.evaluate(test_predictions)

print("===== MODEL EVALUATION =====")
print("Accuracy:", round(accuracy * 100, 2), "%")
print("Weighted Precision:", round(precision * 100, 2), "%")
print("Weighted Recall:", round(recall * 100, 2), "%")
print("F1 Score:", round(f1 * 100, 2), "%")

# COMMAND ----------

final_model = ml_pipeline.fit(ml_training_df)

print("Final model trained on:", ml_training_df.count(), "records")

# COMMAND ----------

all_predictions = final_model.transform(ml_training_df)

print("Full dataset predictions:", all_predictions.count())

display(
    all_predictions
    .select(
        "report_id",
        "clean_text",
        "event_category",
        "prediction"
    )
    .limit(20)
)

# COMMAND ----------

final_label_model = final_model.stages[0]

final_labels = final_label_model.labels

print("===== FINAL EVENT LABELS =====")

for i, label in enumerate(final_labels):
    print(i, "=", label)

ml_predictions_full = (
    all_predictions
    .withColumn(
        "predicted_event",
        F.element_at(
            F.array(*[F.lit(x) for x in final_labels]),
            F.col("prediction").cast("int") + 1
        )
    )
)

display(
    ml_predictions_full
    .select(
        "report_id",
        "event_category",
        "predicted_event"
    )
    .limit(20)
)

# COMMAND ----------

unusable_ml_records = (
    ml_labeled_df
    .filter(
        F.col("clean_text").isNull() |
        (F.trim(F.col("clean_text")) == "")
    )
    .select(
        "report_id",
        "clean_text",
        "event_category"
    )
    .withColumn(
        "predicted_event",
        F.lit("Other")
    )
)

print("Unusable text records:", unusable_ml_records.count())

# COMMAND ----------

usable_predictions = ml_predictions_full.select(
    "report_id",
    "clean_text",
    "event_category",
    "predicted_event"
)

ml_gold_df = (
    usable_predictions
    .unionByName(unusable_ml_records)
    .withColumn(
        "ml_processed_at",
        F.current_timestamp()
    )
)

print("===== FINAL ML GOLD =====")
print("Total predictions:", ml_gold_df.count())

display(
    ml_gold_df
    .groupBy("predicted_event")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

ml_gold_path = f"{GOLD_PATH}ml_predictions/"

ml_gold_df.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(ml_gold_path)

print("======================================")
print("FULL ML GOLD SAVED SUCCESSFULLY")
print("======================================")
print("Records:", ml_gold_df.count())
print("Path:", ml_gold_path)

# COMMAND ----------

print("===== GOLD OUTPUT VALIDATION =====")

for folder in [
    "event_analytics",
    "source_analytics",
    "state_rainfall",
    "ml_predictions"
]:
    path = f"{GOLD_PATH}{folder}/"

    print(f"\n===== {folder} =====")

    files = dbutils.fs.ls(path)

    display(files)

# COMMAND ----------

print("===== FINAL SOURCE ANALYTICS =====")

display(
    gold_source
    .orderBy(F.desc("total_reports"))
)

# COMMAND ----------

print("===== FINAL EVENT ANALYTICS =====")

display(
    gold_event
    .orderBy(F.desc("total_reports"))
)

# COMMAND ----------

print("===== FINAL ML PREDICTIONS =====")

print("Total ML predictions:", ml_gold_df.count())

display(
    ml_gold_df
    .groupBy("predicted_event")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

print("======================================")
print("FINAL PIPELINE VALIDATION")
print("======================================")

print("Bronze records:", bronze_df.count())
print("Silver records:", silver_df.count())
print("Gold-ready records:", gold_ready_df.count())
print("Social Media records:", social_df.count())
print("ML predictions:", ml_gold_df.count())

print("\nNull report IDs in Silver:",
      silver_df.filter(F.col("report_id").isNull()).count())

print("\nDuplicate report IDs in Silver:",
      silver_df.groupBy("report_id")
      .count()
      .filter(F.col("count") > 1)
      .count())

print("\n======================================")
print("PIPELINE COMPLETED SUCCESSFULLY")
print("======================================")
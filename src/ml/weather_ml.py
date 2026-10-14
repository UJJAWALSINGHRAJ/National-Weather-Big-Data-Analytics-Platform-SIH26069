import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# ============================================================
# NATIONAL WEATHER BIG DATA ANALYTICS PLATFORM
# AI/ML EVENT CLASSIFICATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

social_media_file = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "social_media_processed_20260924_143940.csv"
)

gold_dir = PROJECT_ROOT / "data" / "gold"
gold_dir.mkdir(parents=True, exist_ok=True)

output_file = gold_dir / "ml_predictions.csv"


print("=" * 60)
print("AI/ML WEATHER EVENT CLASSIFICATION")
print("=" * 60)


# ------------------------------------------------------------
# 1. Load social media data
# ------------------------------------------------------------

print("\nLoading social media data...")

df = pd.read_csv(social_media_file)

print(f"Records loaded: {len(df)}")


# ------------------------------------------------------------
# 2. Prepare text
# ------------------------------------------------------------

df["text"] = df["text"].fillna("").astype(str)

# Remove empty text
df = df[df["text"].str.strip() != ""].copy()

print(f"Records after text cleaning: {len(df)}")


# ------------------------------------------------------------
# 3. Create training labels
# ------------------------------------------------------------

def classify_event(text):

    text = text.lower()

    if any(word in text for word in [
        "flood",
        "flooding",
        "flooded",
        "inundation"
    ]):
        return "Flooding"

    elif any(word in text for word in [
        "thunderstorm",
        "thunder",
        "lightning"
    ]):
        return "Thunderstorm"

    elif any(word in text for word in [
        "rain",
        "rainfall",
        "raining",
        "downpour"
    ]):
        return "Rainfall"

    elif any(word in text for word in [
        "heatwave",
        "heat wave",
        "extreme heat",
        "hot weather"
    ]):
        return "Heatwave"

    elif any(word in text for word in [
        "fog",
        "dense fog",
        "mist"
    ]):
        return "Fog"

    elif any(word in text for word in [
        "dust storm",
        "duststorm"
    ]):
        return "Dust Storm"

    elif any(word in text for word in [
        "strong wind",
        "high wind",
        "windstorm",
        "gale"
    ]):
        return "Strong Wind"

    else:
        return "Other"


df["event_label"] = df["text"].apply(classify_event)


print("\nGenerated event labels:")

print(
    df["event_label"]
    .value_counts()
)


# ------------------------------------------------------------
# 4. Remove classes with too few records
# ------------------------------------------------------------

label_counts = df["event_label"].value_counts()

valid_labels = label_counts[
    label_counts >= 2
].index

df = df[
    df["event_label"].isin(valid_labels)
].copy()


# ------------------------------------------------------------
# 5. Train/Test split
# ------------------------------------------------------------

X = df["text"]
y = df["event_label"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))


# ------------------------------------------------------------
# 6. TF-IDF
# ------------------------------------------------------------

print("\nCreating TF-IDF features...")

vectorizer = TfidfVectorizer(
    max_features=5000,
    stop_words="english",
    ngram_range=(1, 2)
)

X_train_tfidf = vectorizer.fit_transform(X_train)

X_test_tfidf = vectorizer.transform(X_test)


# ------------------------------------------------------------
# 7. Logistic Regression
# ------------------------------------------------------------

print("\nTraining Logistic Regression model...")

model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

model.fit(
    X_train_tfidf,
    y_train
)


# ------------------------------------------------------------
# 8. Model evaluation
# ------------------------------------------------------------

print("\nEvaluating model...")

y_pred = model.predict(X_test_tfidf)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(
    f"\nModel Accuracy: {accuracy * 100:.2f}%"
)

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ------------------------------------------------------------
# 9. Predict all social-media records
# ------------------------------------------------------------

print("\nGenerating predictions for all records...")

all_tfidf = vectorizer.transform(
    df["text"]
)

df["predicted_event"] = model.predict(
    all_tfidf
)

df["prediction_confidence"] = model.predict_proba(
    all_tfidf
).max(axis=1)


# ------------------------------------------------------------
# 10. Add ML metadata
# ------------------------------------------------------------

df["ml_model"] = "TF-IDF + Logistic Regression"

df["ml_prediction_time"] = datetime.now().strftime(
    "%Y-%m-%d %H:%M:%S"
)


# ------------------------------------------------------------
# 11. Save ML predictions
# ------------------------------------------------------------

prediction_columns = [
    "id",
    "text",
    "source_type",
    "source_name",
    "location",
    "target",
    "event_label",
    "predicted_event",
    "prediction_confidence",
    "ml_model",
    "ml_prediction_time"
]

prediction_columns = [
    column
    for column in prediction_columns
    if column in df.columns
]

ml_predictions = df[
    prediction_columns
].copy()


ml_predictions.to_csv(
    output_file,
    index=False
)


# ------------------------------------------------------------
# 12. Display prediction distribution
# ------------------------------------------------------------

print("\nPrediction Distribution:")

print(
    ml_predictions[
        "predicted_event"
    ].value_counts()
)


print("\nOutput file:")
print(output_file)


print("\n" + "=" * 60)
print("✅ AI/ML MODEL COMPLETED SUCCESSFULLY")
print("=" * 60)

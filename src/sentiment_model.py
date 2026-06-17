"""Train and evaluate the MarketMind sentiment model.

This module uses the cleaned reviews created by the preprocessing pipeline:

    data/processed/marketmind_clean_reviews.csv

It trains a simple TF-IDF + Logistic Regression model and saves the trained
artifacts in the models folder.
"""

import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


PROCESSED_DATA_PATH = "data/processed/marketmind_clean_reviews.csv"
MODEL_OUTPUT_PATH = "models/sentiment_model.pkl"
VECTORIZER_OUTPUT_PATH = "models/tfidf_vectorizer.pkl"


def load_processed_data(file_path):
    """Load the processed CSV file into a pandas DataFrame."""
    return pd.read_csv(file_path)


def prepare_features_and_labels(df):
    """Prepare review text features and sentiment labels for model training."""
    df = df.dropna(subset=["cleaned_review", "sentiment"]).copy()

    X = df["cleaned_review"]
    y = df["sentiment"]

    return X, y


def split_data(X, y):
    """Split features and labels into training and test datasets."""
    return train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )


def train_sentiment_model(X_train, y_train):
    """Train a TF-IDF vectorizer and Logistic Regression sentiment model."""
    vectorizer = TfidfVectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_tfidf, y_train)

    return vectorizer, model


def evaluate_model(model, vectorizer, X_test, y_test):
    """Evaluate the trained model and print common classification metrics."""
    X_test_tfidf = vectorizer.transform(X_test)
    y_pred = model.predict(X_test_tfidf)

    print("Accuracy Score:")
    print(accuracy_score(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))


def save_model_artifacts(model, vectorizer):
    """Save the trained model and vectorizer as joblib pickle files."""
    os.makedirs("models", exist_ok=True)

    joblib.dump(model, MODEL_OUTPUT_PATH)
    joblib.dump(vectorizer, VECTORIZER_OUTPUT_PATH)

    print(f"\nSaved model to: {MODEL_OUTPUT_PATH}")
    print(f"Saved vectorizer to: {VECTORIZER_OUTPUT_PATH}")


def predict_sentiment(
    review_text,
    model_path=MODEL_OUTPUT_PATH,
    vectorizer_path=VECTORIZER_OUTPUT_PATH,
):
    """Predict sentiment for one review using saved model artifacts."""
    # Load the already-trained model and vectorizer from disk.
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    # The vectorizer expects a list-like input, even for one review.
    review_tfidf = vectorizer.transform([review_text])

    # model.predict returns a list/array, so return the first prediction.
    predicted_sentiment = model.predict(review_tfidf)[0]

    return predicted_sentiment


if __name__ == "__main__":
    reviews_df = load_processed_data(PROCESSED_DATA_PATH)
    X, y = prepare_features_and_labels(reviews_df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    trained_vectorizer, trained_model = train_sentiment_model(X_train, y_train)

    evaluate_model(trained_model, trained_vectorizer, X_test, y_test)
    save_model_artifacts(trained_model, trained_vectorizer)

    # Optional quick prediction examples using the saved model artifacts.
    example_reviews = [
        "this product is very good and worth the money",
        "very bad product waste of money",
        "okay product average quality",
    ]

    print("\nExample Predictions:")
    for review in example_reviews:
        sentiment = predict_sentiment(review)
        print(f"Review: {review}")
        print(f"Predicted sentiment: {sentiment}\n")

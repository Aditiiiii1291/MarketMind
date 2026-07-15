"""Data preprocessing utilities for MarketMind product review data.

This module converts the raw product review CSV into a cleaned dataset that can
be used later for sentiment analysis, complaint mining, and scoring workflows.
"""

import re

import pandas as pd

try:
    from src.config import PROCESSED_REVIEWS_PATH, RAW_REVIEWS_PATH
    from src.logger import logger
    from src.utils.file_io import ensure_parent_dir, load_csv
except ImportError:
    from config import PROCESSED_REVIEWS_PATH, RAW_REVIEWS_PATH
    from logger import logger
    from utils.file_io import ensure_parent_dir, load_csv


DEFAULT_INPUT_PATH = RAW_REVIEWS_PATH
DEFAULT_OUTPUT_PATH = PROCESSED_REVIEWS_PATH


def load_raw_data(file_path):
    """Load the raw CSV dataset into a pandas DataFrame."""
    return load_csv(
        file_path,
        description="Raw review CSV",
        encoding="latin1",
        low_memory=False,
    )


def standardize_columns(df):
    """Rename raw dataset columns to simpler snake_case names."""
    column_names = {
        "ProductName": "product_name",
        "ProductPrice": "product_price",
        "Rate": "rating",
        "Review": "review_title",
        "Summary": "review_text",
        "Sentiment": "sentiment",
    }

    return df.rename(columns=column_names)


def create_full_review(df):
    """Combine review title and review text into one full_review column."""
    df = df.copy()

    review_title = df["review_title"].fillna("").astype(str)
    review_text = df["review_text"].fillna("").astype(str)

    df["full_review"] = (review_title + " " + review_text).str.strip()
    df["full_review"] = df["full_review"].replace("", pd.NA)

    return df


def clean_price_column(df):
    """Clean product_price and store the numeric result in clean_price."""
    df = df.copy()

    price_text = df["product_price"].fillna("").astype(str)
    price_text = price_text.str.replace(r"[^0-9.]", "", regex=True)

    df["clean_price"] = pd.to_numeric(price_text, errors="coerce")

    return df


def clean_rating_column(df):
    """Convert rating values to numeric values."""
    df = df.copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    return df


def clean_review_text(text):
    """Clean review text while keeping the logic easy to read and change."""
    if pd.isna(text):
        return pd.NA

    text = str(text).lower()

    # Remove website links.
    text = re.sub(r"http\S+|www\S+", " ", text)

    # Remove punctuation and special characters, keeping letters and numbers.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Replace repeated spaces with one space.
    text = re.sub(r"\s+", " ", text).strip()

    if text == "":
        return pd.NA

    return text


def prepare_dataset(input_path, output_path):
    """Run the full preprocessing pipeline and save the cleaned dataset."""
    df = load_raw_data(input_path)
    df = standardize_columns(df)
    df = create_full_review(df)
    df = clean_price_column(df)
    df = clean_rating_column(df)

    df["cleaned_review"] = df["full_review"].apply(clean_review_text)
    df["cleaned_review"] = df["cleaned_review"].str.strip()
    df["cleaned_review"] = df["cleaned_review"].replace("", pd.NA)
    df = df.dropna(subset=["cleaned_review"])

    final_columns = [
        "product_name",
        "clean_price",
        "rating",
        "full_review",
        "cleaned_review",
        "sentiment",
    ]
    df = df[final_columns]

    df = df.dropna(
        subset=[
            "full_review",
            "cleaned_review",
            "sentiment",
            "rating",
        ]
    )

    output_path = ensure_parent_dir(output_path)

    final_columns = [
        "product_name",
        "clean_price",
        "rating",
        "full_review",
        "cleaned_review",
        "sentiment",
    ]
    df = df[final_columns]

    invalid_text_values = ["", "nan", "none", "null"]
    for text_column in ["full_review", "cleaned_review"]:
        not_missing_text = df[text_column].notna()
        df.loc[not_missing_text, text_column] = (
            df.loc[not_missing_text, text_column].astype(str).str.strip()
        )

        invalid_text = df[text_column].str.lower().isin(invalid_text_values)
        df.loc[invalid_text, text_column] = pd.NA

    df = df.dropna(
        subset=[
            "product_name",
            "rating",
            "full_review",
            "cleaned_review",
            "sentiment",
        ]
    )

    df.to_csv(output_path, index=False)

    return df


if __name__ == "__main__":
    try:
        prepare_dataset(DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH)
    except FileNotFoundError as error:
        logger.error(error)
        raise SystemExit(1)

import pandas as pd
import sys
from pathlib import Path
import sqlite3
from datetime import datetime

from src.database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data_preprocessing import clean_review_text


INPUT_PATH = "data/raw/mini_electronics_reviews.csv"

REQUIRED_COLUMNS = [
    "product_title",
    "review_body",
    "stars",
    "label",
    "price",
]


def validate_required_columns(df):
    missing_columns = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        print("Missing columns:", missing_columns)
        return False

    print("All required columns are present.")
    return True

def get_or_create_source_id(connection, source_name, source_path):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT source_id
        FROM dataset_sources
        WHERE source_name = ?
        """,
        (source_name,),
    )

    existing_source = cursor.fetchone()

    if existing_source is not None:
        return existing_source[0]

    imported_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO dataset_sources (
            source_name,
            source_path,
            imported_at,
            description
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            source_name,
            source_path,
            imported_at,
            "Mini electronics practice dataset",
        ),
    )

    connection.commit()

    return cursor.lastrowid
def convert_to_marketmind_schema(df):
    transformed_df = pd.DataFrame()

    transformed_df["product_name"] = df["product_title"]
    transformed_df["clean_price"] = pd.to_numeric(df["price"], errors="coerce")
    transformed_df["rating"] = pd.to_numeric(df["stars"], errors="coerce")
    transformed_df["full_review"] = df["review_body"].astype(str)
    transformed_df["cleaned_review"] = transformed_df["full_review"].apply(clean_review_text)
    transformed_df["sentiment"] = df["label"].astype(str).str.lower().str.strip()
    transformed_df["category"] = "Electronics"

    return transformed_df


def validate_transformed_rows(transformed_df):
    # Validate rows before database insertion so incomplete or invalid data is not saved.
    invalid_product_name = transformed_df["product_name"].isna() | (
        transformed_df["product_name"].astype(str).str.strip() == ""
    )
    invalid_review = transformed_df["cleaned_review"].isna() | (
        transformed_df["cleaned_review"].astype(str).str.strip() == ""
    )
    invalid_rating = transformed_df["rating"].isna() | ~transformed_df["rating"].between(1, 5)
    invalid_sentiment = ~transformed_df["sentiment"].isin(
        ["negative", "neutral", "positive"]
    )

    invalid_rows = (
        invalid_product_name | invalid_review | invalid_rating | invalid_sentiment
    )
    valid_df = transformed_df[~invalid_rows]

    print("Valid rows:", len(valid_df))
    print("Invalid rows:", invalid_rows.sum())

    return valid_df


def main():
    try:
        df = pd.read_csv(INPUT_PATH)
    except FileNotFoundError:
        print("CSV file was not found.")
        return
        connection = get_connection("data/marketmind.db")

    source_id = get_or_create_source_id(
        connection,
        "mini_electronics_v1",
        INPUT_PATH,
    )

    print()
    print("Dataset source is ready.")
    print("Source name: mini_electronics_v1")
    print("Source ID:", source_id)

    connection.close()
    print("Rows read:", len(df))
    print("Columns found:", list(df.columns))
    print()

    if not validate_required_columns(df):
        return

    print()
    print("Dataset is ready for conversion.")

    transformed_df = convert_to_marketmind_schema(df)

    print()
    print("Converted MarketMind format:")
    print(transformed_df.head())

    print()
    print("Converted columns:")
    print(transformed_df.columns.tolist())

    print()
    valid_df = validate_transformed_rows(transformed_df)

    print("\nFinal validated dataset:")
    print(valid_df)


if __name__ == "__main__":
    main()

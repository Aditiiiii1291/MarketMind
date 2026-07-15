r"""Import an external review CSV into the MarketMind SQLite database.

Run from the project root:

    python scripts\ingest_dataset.py

Use --dry-run to validate and preview the import without changing the database.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_preprocessing import clean_review_text
from src.config import DATABASE_PATH, MINI_ELECTRONICS_REVIEWS_PATH
from src.database import (
    create_stable_product_id,
    create_stable_review_id,
    get_connection,
    initialize_database,
    normalize_product_name,
)
from src.logger import logger
from src.utils.file_io import display_path, load_csv, resolve_project_path


DEFAULT_INPUT_PATH = MINI_ELECTRONICS_REVIEWS_PATH
DEFAULT_SOURCE_NAME = "mini_electronics_v1"
DEFAULT_CATEGORY = "Electronics"
DEFAULT_DATABASE_PATH = DATABASE_PATH

REQUIRED_RAW_COLUMNS = [
    "product_title",
    "review_body",
    "stars",
    "label",
    "price",
]

MARKETMIND_COLUMNS = [
    "product_name",
    "clean_price",
    "rating",
    "full_review",
    "cleaned_review",
    "sentiment",
    "category",
]

VALID_SENTIMENTS = {"negative", "neutral", "positive"}


def parse_arguments():
    """Read command-line options for the import."""
    parser = argparse.ArgumentParser(
        description="Import an external review CSV into data/marketmind.db."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Input CSV path.",
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help="Unique name for this dataset source.",
    )
    parser.add_argument(
        "--category",
        default=DEFAULT_CATEGORY,
        help="Category to assign to imported products.",
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE_PATH),
        help="SQLite database path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview the import without writing to the database.",
    )

    return parser.parse_args()


def read_external_csv(input_path):
    """Load the external CSV file."""
    return load_csv(input_path, description="Input CSV")


def validate_raw_columns(raw_df):
    """Require the external CSV to contain exactly the expected columns."""
    found_columns = list(raw_df.columns)
    missing_columns = [
        column for column in REQUIRED_RAW_COLUMNS if column not in found_columns
    ]
    unexpected_columns = [
        column for column in found_columns if column not in REQUIRED_RAW_COLUMNS
    ]

    if missing_columns or unexpected_columns:
        print("Raw column validation failed.")
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
        if unexpected_columns:
            print(f"Unexpected columns: {unexpected_columns}")
        print(f"Required columns: {REQUIRED_RAW_COLUMNS}")
        return False

    print("Raw column validation passed.")
    return True


def convert_to_marketmind_schema(raw_df, category):
    """Convert the external CSV format into the MarketMind review format."""
    converted_df = pd.DataFrame()
    converted_df["product_name"] = raw_df["product_title"].astype("string").str.strip()
    converted_df["clean_price"] = pd.to_numeric(raw_df["price"], errors="coerce")
    converted_df["rating"] = pd.to_numeric(raw_df["stars"], errors="coerce")
    converted_df["full_review"] = raw_df["review_body"].astype("string").str.strip()
    converted_df["cleaned_review"] = converted_df["full_review"].apply(clean_review_text)
    converted_df["sentiment"] = raw_df["label"].astype("string").str.lower().str.strip()
    converted_df["category"] = category

    return converted_df[MARKETMIND_COLUMNS]


def validate_converted_rows(converted_df):
    """Keep only rows that are safe to insert into the database."""
    valid_rows = []
    invalid_count = 0

    for _, row in converted_df.iterrows():
        product_name = safe_text(row["product_name"])
        cleaned_review = safe_text(row["cleaned_review"])
        sentiment = safe_text(row["sentiment"]).lower()
        rating = row["rating"]

        row_is_valid = (
            product_name != ""
            and cleaned_review != ""
            and pd.notna(rating)
            and 1 <= float(rating) <= 5
            and sentiment in VALID_SENTIMENTS
        )

        if row_is_valid:
            clean_row = row.copy()
            clean_row["product_name"] = product_name
            clean_row["full_review"] = safe_text(row["full_review"])
            clean_row["cleaned_review"] = cleaned_review
            clean_row["sentiment"] = sentiment
            clean_row["rating"] = float(rating)
            valid_rows.append(clean_row)
        else:
            invalid_count += 1

    valid_df = pd.DataFrame(valid_rows, columns=MARKETMIND_COLUMNS)

    print(f"Converted row validation complete: {len(valid_df)} valid, {invalid_count} invalid.")
    return valid_df, invalid_count


def safe_text(value):
    """Convert non-empty values to stripped text and treat missing values as blank."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def get_or_create_dataset_source(connection, source_name, source_path):
    """Find an existing dataset source or create a new one."""
    existing_source = connection.execute(
        """
        SELECT source_id
        FROM dataset_sources
        WHERE source_name = ?
        """,
        (source_name,),
    ).fetchone()

    if existing_source is not None:
        return existing_source[0], False

    imported_at = datetime.now().isoformat(timespec="seconds")
    cursor = connection.execute(
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
            f"External review CSV imported from {source_path}",
        ),
    )

    return cursor.lastrowid, True


def get_or_create_product(connection, row, source_id, created_at):
    """Find an existing product by normalized name or insert a new product."""
    product_name = row["product_name"]
    normalized_name = normalize_product_name(product_name)

    existing_product = connection.execute(
        """
        SELECT product_id
        FROM products
        WHERE normalized_name = ?
        LIMIT 1
        """,
        (normalized_name,),
    ).fetchone()

    if existing_product is not None:
        return existing_product[0], False

    product_id = create_stable_product_id(normalized_name)
    connection.execute(
        """
        INSERT INTO products (
            product_id,
            product_name,
            normalized_name,
            category,
            clean_price,
            source_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            product_name,
            normalized_name,
            row["category"],
            none_if_missing(row["clean_price"]),
            source_id,
            created_at,
        ),
    )

    return product_id, True


def insert_review(connection, row, product_id, source_id, source_name, created_at):
    """Insert one review and return True when a new row was created."""
    review_id = create_stable_review_id(
        product_id,
        row["cleaned_review"],
        row["rating"],
        source_name,
    )

    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO reviews (
            review_id,
            product_id,
            rating,
            full_review,
            cleaned_review,
            sentiment,
            source_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            product_id,
            row["rating"],
            row["full_review"],
            row["cleaned_review"],
            row["sentiment"],
            source_id,
            created_at,
        ),
    )

    return cursor.rowcount == 1


def none_if_missing(value):
    """Convert pandas missing values to None before inserting into SQLite."""
    if pd.isna(value):
        return None

    return value


def count_ready_products(valid_df):
    """Count unique valid products by normalized name."""
    normalized_names = {
        normalize_product_name(product_name) for product_name in valid_df["product_name"]
    }
    normalized_names.discard("")

    return len(normalized_names)


def import_rows(valid_df, database_path, source_name, source_path):
    """Insert valid products and reviews inside one database transaction."""
    summary = {
        "source_created": False,
        "source_id": None,
        "products_inserted": 0,
        "products_reused": 0,
        "reviews_inserted": 0,
        "reviews_skipped_duplicates": 0,
    }

    connection = get_connection(database_path)
    try:
        initialize_database(connection)
        with connection:
            source_id, source_created = get_or_create_dataset_source(
                connection,
                source_name,
                source_path,
            )
            summary["source_id"] = source_id
            summary["source_created"] = source_created

            created_at = datetime.now().isoformat(timespec="seconds")
            product_ids_by_name = {}

            for _, row in valid_df.iterrows():
                normalized_name = normalize_product_name(row["product_name"])

                if normalized_name in product_ids_by_name:
                    product_id = product_ids_by_name[normalized_name]
                else:
                    product_id, product_created = get_or_create_product(
                        connection,
                        row,
                        source_id,
                        created_at,
                    )
                    product_ids_by_name[normalized_name] = product_id
                    if product_created:
                        summary["products_inserted"] += 1
                    else:
                        summary["products_reused"] += 1

                review_inserted = insert_review(
                    connection,
                    row,
                    product_id,
                    source_id,
                    source_name,
                    created_at,
                )
                if review_inserted:
                    summary["reviews_inserted"] += 1
                else:
                    summary["reviews_skipped_duplicates"] += 1
    finally:
        connection.close()

    return summary


def print_preview(args, input_path, database_path, raw_df, valid_df, invalid_count):
    """Print the validation summary before an import or dry run."""
    print("MarketMind external dataset ingestion")
    print(f"Input CSV: {display_path(input_path)}")
    print(f"Database: {display_path(database_path)}")
    print(f"Source name: {args.source_name}")
    print(f"Category: {args.category}")
    print(f"Rows read: {len(raw_df)}")
    print(f"Valid rows ready: {len(valid_df)}")
    print(f"Invalid rows skipped: {invalid_count}")
    print(f"Products ready: {count_ready_products(valid_df)}")
    print(f"Reviews ready: {len(valid_df)}")


def print_import_summary(summary):
    """Print the final database import results."""
    source_status = "created" if summary["source_created"] else "reused"

    print("Import summary")
    print(f"Dataset source: {source_status} (source_id={summary['source_id']})")
    print(f"Products inserted: {summary['products_inserted']}")
    print(f"Products reused: {summary['products_reused']}")
    print(f"Reviews inserted: {summary['reviews_inserted']}")
    print(f"Duplicate reviews skipped: {summary['reviews_skipped_duplicates']}")


def main():
    """Run the full CSV-to-database ingestion pipeline."""
    args = parse_arguments()
    input_path = resolve_project_path(args.input)
    database_path = resolve_project_path(args.database)
    source_path = display_path(input_path)

    try:
        raw_df = read_external_csv(input_path)
    except FileNotFoundError as error:
        logger.error(error)
        print(error)
        return 1

    if not validate_raw_columns(raw_df):
        return 1

    converted_df = convert_to_marketmind_schema(raw_df, args.category)
    valid_df, invalid_count = validate_converted_rows(converted_df)

    print_preview(args, input_path, database_path, raw_df, valid_df, invalid_count)

    if args.dry_run:
        print("Dry run complete. No database changes were made.")
        return 0

    summary = import_rows(valid_df, database_path, args.source_name, source_path)
    print_import_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

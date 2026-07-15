"""Migrate MarketMind's current processed CSV into a local SQLite database.

This Phase 9A script creates `data/marketmind.db` from the existing processed
CSV. It does not change the CSV file or replace the existing CSV-based app and
ML modules.
"""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import (  # noqa: E402
    create_stable_product_id,
    create_stable_review_id,
    get_connection,
    get_database_counts,
    initialize_database,
    normalize_product_name,
)
from src.config import DATABASE_PATH, PROCESSED_REVIEWS_PATH  # noqa: E402
from src.logger import logger  # noqa: E402
from src.utils.file_io import require_file  # noqa: E402


DEFAULT_INPUT_PATH = PROCESSED_REVIEWS_PATH
DEFAULT_DATABASE_PATH = DATABASE_PATH
DEFAULT_SOURCE_NAME = "marketmind_clean_reviews_csv"
REQUIRED_COLUMNS = {
    "product_name",
    "clean_price",
    "rating",
    "full_review",
    "cleaned_review",
    "sentiment",
}
VALID_SENTIMENTS = {"negative", "neutral", "positive"}
CHUNK_SIZE = 5000
UNCATEGORIZED = "Uncategorized"


def parse_args():
    """Parse command-line arguments for the CSV migration."""
    parser = argparse.ArgumentParser(
        description="Migrate MarketMind processed reviews CSV to SQLite."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Processed CSV path to migrate.",
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE_PATH),
        help="SQLite database path to create or update.",
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help="Dataset source name stored in dataset_sources.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing SQLite database before migration.",
    )

    return parser.parse_args()


def utc_now_iso():
    """Return a consistent UTC timestamp for imported rows."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value):
    """Return stripped text or an empty string for missing CSV values."""
    if value is None:
        return ""

    return str(value).strip()


def parse_optional_float(value):
    """Parse an optional float field, returning None when it is blank."""
    text = clean_text(value)
    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_required_rating(value):
    """Parse a required numeric rating."""
    text = clean_text(value)
    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def validate_csv_columns(input_path):
    """Validate that the CSV contains the expected processed-review columns."""
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])

    missing_columns = sorted(REQUIRED_COLUMNS - fieldnames)
    if missing_columns:
        raise ValueError(
            "CSV is missing required column(s): " + ", ".join(missing_columns)
        )


def ensure_dataset_source(connection, source_name, source_path):
    """Insert or return the dataset source row for this migration."""
    imported_at = utc_now_iso()
    connection.execute(
        """
        INSERT OR IGNORE INTO dataset_sources (
            source_name,
            source_path,
            imported_at,
            description
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            source_name,
            str(source_path),
            imported_at,
            "Current processed MarketMind CSV migration.",
        ),
    )
    connection.execute(
        """
        UPDATE dataset_sources
        SET source_path = ?, imported_at = ?
        WHERE source_name = ?
        """,
        (str(source_path), imported_at, source_name),
    )
    source_id = connection.execute(
        "SELECT source_id FROM dataset_sources WHERE source_name = ?",
        (source_name,),
    ).fetchone()[0]

    return source_id


def iter_csv_chunks(input_path, chunk_size):
    """Yield lists of CSV rows so each chunk can be migrated in a transaction."""
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        chunk = []

        for row in reader:
            chunk.append(row)
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []

        if chunk:
            yield chunk


def prepare_row(row, source_name, source_id, created_at):
    """Validate and convert one CSV row into database records."""
    product_name = clean_text(row.get("product_name"))
    cleaned_review = clean_text(row.get("cleaned_review"))
    full_review = clean_text(row.get("full_review"))
    sentiment = clean_text(row.get("sentiment")).lower()
    rating = parse_required_rating(row.get("rating"))

    if product_name == "" or cleaned_review == "":
        return None
    if rating is None:
        return None
    if sentiment not in VALID_SENTIMENTS:
        return None

    normalized_name = normalize_product_name(product_name)
    if normalized_name == "":
        return None

    clean_price = parse_optional_float(row.get("clean_price"))
    product_id = create_stable_product_id(normalized_name)
    review_id = create_stable_review_id(
        product_id,
        cleaned_review,
        rating,
        source_name,
    )

    product_values = (
        product_id,
        product_name,
        normalized_name,
        UNCATEGORIZED,
        clean_price,
        source_id,
        created_at,
    )
    review_values = (
        review_id,
        product_id,
        rating,
        full_review or None,
        cleaned_review,
        sentiment,
        source_id,
        created_at,
    )

    return product_values, review_values


def migrate_chunk(connection, chunk, source_name, source_id, created_at):
    """Migrate one chunk of CSV rows inside the active transaction."""
    stats = {
        "valid_rows": 0,
        "products_inserted": 0,
        "reviews_inserted": 0,
        "duplicate_reviews": 0,
        "invalid_rows": 0,
    }

    for row in chunk:
        prepared_row = prepare_row(row, source_name, source_id, created_at)
        if prepared_row is None:
            stats["invalid_rows"] += 1
            continue

        product_values, review_values = prepared_row
        stats["valid_rows"] += 1

        product_cursor = connection.execute(
            """
            INSERT OR IGNORE INTO products (
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
            product_values,
        )
        if product_cursor.rowcount == 1:
            stats["products_inserted"] += 1

        review_cursor = connection.execute(
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
            review_values,
        )
        if review_cursor.rowcount == 1:
            stats["reviews_inserted"] += 1
        else:
            stats["duplicate_reviews"] += 1

    return stats


def add_stats(total_stats, chunk_stats):
    """Add chunk counters into the migration total."""
    for key, value in chunk_stats.items():
        total_stats[key] += value


def fetch_sentiment_distribution(connection):
    """Return review counts grouped by sentiment."""
    return connection.execute(
        """
        SELECT sentiment, COUNT(*) AS review_count
        FROM reviews
        GROUP BY sentiment
        ORDER BY sentiment
        """
    ).fetchall()


def fetch_rating_null_count(connection):
    """Return the number of reviews with a missing rating."""
    return connection.execute(
        "SELECT COUNT(*) FROM reviews WHERE rating IS NULL"
    ).fetchone()[0]


def fetch_uncategorized_product_count(connection):
    """Return the number of products using the default category."""
    return connection.execute(
        "SELECT COUNT(*) FROM products WHERE category = ?",
        (UNCATEGORIZED,),
    ).fetchone()[0]


def fetch_top_products_by_review_count(connection, limit=10):
    """Return top products by number of migrated reviews."""
    return connection.execute(
        """
        SELECT products.product_name, COUNT(reviews.review_id) AS review_count
        FROM products
        JOIN reviews ON reviews.product_id = products.product_id
        GROUP BY products.product_id, products.product_name
        ORDER BY review_count DESC, products.product_name ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def print_summary(total_stats, counts, connection):
    """Print migration and data-quality summaries."""
    print("\nMigration summary")
    print("-----------------")
    print(f"Rows read: {total_stats['rows_read']}")
    print(f"Valid rows processed: {total_stats['valid_rows']}")
    print(f"Products inserted: {total_stats['products_inserted']}")
    print(f"Reviews inserted: {total_stats['reviews_inserted']}")
    print(f"Duplicate reviews skipped: {total_stats['duplicate_reviews']}")
    print(f"Invalid rows skipped: {total_stats['invalid_rows']}")
    print(f"Final total products: {counts['products']}")
    print(f"Final total reviews: {counts['reviews']}")

    print("\nData-quality checks")
    print("-------------------")
    print(f"Total products: {counts['products']}")
    print(f"Total reviews: {counts['reviews']}")

    print("\nSentiment distribution:")
    for sentiment, review_count in fetch_sentiment_distribution(connection):
        print(f"- {sentiment}: {review_count}")

    print(f"\nRating null count: {fetch_rating_null_count(connection)}")
    print(
        "Uncategorized product count: "
        f"{fetch_uncategorized_product_count(connection)}"
    )

    print("\nTop 10 products by review count:")
    for product_name, review_count in fetch_top_products_by_review_count(connection):
        safe_product_name = (
            str(product_name).encode("ascii", errors="replace").decode("ascii")
        )
        print(f"- {safe_product_name}: {review_count}")


def main():
    """Run the CSV-to-SQLite migration."""
    args = parse_args()
    try:
        input_path = require_file(args.input, "Processed CSV")
    except FileNotFoundError as error:
        logger.error(error)
        print(error)
        return 1
    database_path = Path(args.database)

    if args.reset and database_path.exists():
        print(f"WARNING: --reset enabled. Deleting existing database: {database_path}")
        database_path.unlink()

    try:
        validate_csv_columns(input_path)
    except ValueError as error:
        logger.error(error)
        print(error)
        return 1

    total_stats = {
        "rows_read": 0,
        "valid_rows": 0,
        "products_inserted": 0,
        "reviews_inserted": 0,
        "duplicate_reviews": 0,
        "invalid_rows": 0,
    }
    created_at = utc_now_iso()

    with get_connection(database_path) as connection:
        initialize_database(connection)
        source_id = ensure_dataset_source(
            connection,
            args.source_name,
            input_path,
        )
        connection.commit()

        for chunk in iter_csv_chunks(input_path, CHUNK_SIZE):
            total_stats["rows_read"] += len(chunk)
            with connection:
                chunk_stats = migrate_chunk(
                    connection,
                    chunk,
                    args.source_name,
                    source_id,
                    created_at,
                )
            add_stats(total_stats, chunk_stats)

        counts = get_database_counts(connection)
        print_summary(total_stats, counts, connection)


if __name__ == "__main__":
    raise SystemExit(main())

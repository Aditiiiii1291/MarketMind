"""Database helpers for the MarketMind persistence layer.

SQLite remains the default database. PostgreSQL support is selected through
configuration and kept behind this module so services and APIs do not know
which database implementation is active.
"""

import hashlib
import re

try:
    from src.database.connection import (
        DatabaseConfigurationError,
        execute,
        get_connection,
        get_database_type,
        initialize_postgres_schema,
        is_integrity_error,
        is_postgres_connection,
        is_sqlite_connection,
        read_sql_query,
        validate_database_config,
    )
except ImportError:
    from database.connection import (
        DatabaseConfigurationError,
        execute,
        get_connection,
        get_database_type,
        initialize_postgres_schema,
        is_integrity_error,
        is_postgres_connection,
        is_sqlite_connection,
        read_sql_query,
        validate_database_config,
    )


DATASET_SOURCE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS dataset_sources (
        source_id INTEGER PRIMARY KEY,
        source_name TEXT NOT NULL UNIQUE,
        source_path TEXT,
        imported_at TEXT NOT NULL,
        description TEXT
    )
"""
PRODUCT_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Uncategorized',
        clean_price REAL,
        source_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(source_id) REFERENCES dataset_sources(source_id)
    )
"""
REVIEW_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS reviews (
        review_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        rating REAL,
        full_review TEXT,
        cleaned_review TEXT NOT NULL,
        sentiment TEXT,
        source_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        FOREIGN KEY(source_id) REFERENCES dataset_sources(source_id)
    )
"""
USER_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
"""
UPLOAD_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        rows_processed INTEGER NOT NULL,
        products_added INTEGER NOT NULL,
        reviews_added INTEGER NOT NULL,
        duplicates_skipped INTEGER NOT NULL,
        uploaded_at TEXT NOT NULL
    )
"""
INDEX_SQL = [
    """
    CREATE INDEX IF NOT EXISTS idx_products_normalized_name
    ON products(normalized_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_product_id
    ON reviews(product_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_sentiment
    ON reviews(sentiment)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_rating
    ON reviews(rating)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reviews_source_id
    ON reviews(source_id)
    """,
]


def initialize_database(connection):
    """Create MarketMind tables for the active database implementation."""
    if is_postgres_connection(connection):
        initialize_postgres_schema(connection)
        return

    for statement in [
        DATASET_SOURCE_TABLE_SQL,
        PRODUCT_TABLE_SQL,
        REVIEW_TABLE_SQL,
        USER_TABLE_SQL,
        UPLOAD_TABLE_SQL,
    ]:
        execute(connection, statement)

    create_indexes(connection)
    connection.commit()


def normalize_product_name(product_name):
    """Normalize a product name for stable matching and ID generation."""
    if product_name is None:
        return ""

    normalized_name = str(product_name).strip().lower()
    normalized_name = re.sub(r"\s+", " ", normalized_name)

    return normalized_name


def create_stable_product_id(normalized_name):
    """Create a deterministic, readable product ID from a normalized name."""
    digest = hashlib.sha256(str(normalized_name).encode("utf-8")).hexdigest()

    return f"prod_{digest[:16]}"


def create_stable_review_id(product_id, cleaned_review, rating, source_name):
    """Create a deterministic, readable review ID from review identity fields."""
    identity_text = "|".join(
        [
            str(product_id),
            str(cleaned_review).strip().lower(),
            str(rating),
            str(source_name),
        ]
    )
    digest = hashlib.sha256(identity_text.encode("utf-8")).hexdigest()

    return f"rev_{digest[:24]}"


def create_indexes(connection):
    """Create indexes used by product lookup and review analysis queries."""
    for statement in INDEX_SQL:
        execute(connection, statement)


def get_database_counts(connection):
    """Return basic table counts for quick migration validation."""
    product_count = execute(connection, "SELECT COUNT(*) FROM products").fetchone()[0]
    review_count = execute(connection, "SELECT COUNT(*) FROM reviews").fetchone()[0]
    source_count = execute(
        connection,
        "SELECT COUNT(*) FROM dataset_sources",
    ).fetchone()[0]

    return {
        "dataset_sources": source_count,
        "products": product_count,
        "reviews": review_count,
    }

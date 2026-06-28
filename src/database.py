"""SQLite database helpers for the MarketMind local data layer.

Phase 9A adds these helpers without replacing the existing CSV-based modules.
They are intentionally small and beginner-friendly so later phases can reuse
the same schema from scripts, tests, and the Streamlit dashboard.
"""

import hashlib
import re
import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = Path("data") / "marketmind.db"


def get_connection(db_path=DEFAULT_DATABASE_PATH):
    """Open a SQLite connection and enable foreign-key checks."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database(connection):
    """Create the MarketMind SQLite tables if they do not exist."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_sources (
            source_id INTEGER PRIMARY KEY,
            source_name TEXT NOT NULL UNIQUE,
            source_path TEXT,
            imported_at TEXT NOT NULL,
            description TEXT
        )
        """
    )

    connection.execute(
        """
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
    )

    connection.execute(
        """
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
    )

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
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_normalized_name
        ON products(normalized_name)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products(category)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id
        ON reviews(product_id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reviews_sentiment
        ON reviews(sentiment)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reviews_rating
        ON reviews(rating)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reviews_source_id
        ON reviews(source_id)
        """
    )


def get_database_counts(connection):
    """Return basic table counts for quick migration validation."""
    product_count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    review_count = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    source_count = connection.execute(
        "SELECT COUNT(*) FROM dataset_sources"
    ).fetchone()[0]

    return {
        "dataset_sources": source_count,
        "products": product_count,
        "reviews": review_count,
    }

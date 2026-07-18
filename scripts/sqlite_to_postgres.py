r"""Copy MarketMind data from SQLite into PostgreSQL.

Run from the project root after configuring MARKETMIND_DATABASE_URL:

    python scripts\sqlite_to_postgres.py

The script preserves primary keys and timestamps, initializes the PostgreSQL
schema, and verifies row counts after the copy.
"""

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATABASE_PATH, DATABASE_URL  # noqa: E402
from src.database import execute, get_connection, initialize_database  # noqa: E402
from src.database.connection import validate_database_config  # noqa: E402
from src.logger import logger  # noqa: E402


TABLES = [
    {
        "name": "dataset_sources",
        "columns": [
            "source_id",
            "source_name",
            "source_path",
            "imported_at",
            "description",
        ],
        "primary_key": "source_id",
        "order_by": "source_id",
    },
    {
        "name": "users",
        "columns": ["id", "username", "email", "password_hash", "created_at"],
        "primary_key": "id",
        "order_by": "id",
    },
    {
        "name": "uploads",
        "columns": [
            "id",
            "user_id",
            "filename",
            "rows_processed",
            "products_added",
            "reviews_added",
            "duplicates_skipped",
            "uploaded_at",
        ],
        "primary_key": "id",
        "order_by": "id",
    },
    {
        "name": "products",
        "columns": [
            "product_id",
            "product_name",
            "normalized_name",
            "category",
            "clean_price",
            "source_id",
            "created_at",
        ],
        "primary_key": "product_id",
        "order_by": "product_id",
    },
    {
        "name": "reviews",
        "columns": [
            "review_id",
            "product_id",
            "rating",
            "full_review",
            "cleaned_review",
            "sentiment",
            "source_id",
            "created_at",
        ],
        "primary_key": "review_id",
        "order_by": "review_id",
    },
]
IDENTITY_COLUMNS = {
    "dataset_sources": "source_id",
    "users": "id",
    "uploads": "id",
}


def parse_args():
    """Parse command-line options for SQLite-to-PostgreSQL migration."""
    parser = argparse.ArgumentParser(
        description="Copy MarketMind SQLite data into PostgreSQL."
    )
    parser.add_argument(
        "--sqlite",
        default=str(DATABASE_PATH),
        help="Source SQLite database path.",
    )
    parser.add_argument(
        "--postgres-url",
        default=DATABASE_URL,
        help="Target PostgreSQL connection URL.",
    )

    return parser.parse_args()


def fetch_rows(connection, table):
    """Fetch all rows for one migration table from SQLite."""
    column_sql = ", ".join(table["columns"])
    try:
        cursor = execute(
            connection,
            f"""
            SELECT {column_sql}
            FROM {table["name"]}
            ORDER BY {table["order_by"]}
            """,
        )
    except Exception as error:
        if "no such table" in str(error).lower():
            return []
        raise

    return cursor.fetchall()


def insert_rows(connection, table, rows):
    """Insert rows into PostgreSQL while preserving primary keys."""
    if not rows:
        return 0

    columns_sql = ", ".join(table["columns"])
    placeholders = ", ".join(["?"] * len(table["columns"]))
    sql = f"""
        INSERT INTO {table["name"]} ({columns_sql})
        VALUES ({placeholders})
        ON CONFLICT ({table["primary_key"]}) DO NOTHING
    """

    inserted = 0
    for row in rows:
        cursor = execute(connection, sql, tuple(row))
        inserted += cursor.rowcount

    return inserted


def count_rows(connection, table_name):
    """Return row count for one table."""
    return execute(connection, f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def reset_identity_sequences(connection):
    """Advance PostgreSQL identity sequences after explicit ID inserts."""
    for table_name, column_name in IDENTITY_COLUMNS.items():
        execute(
            connection,
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', '{column_name}'),
                COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                (SELECT COUNT(*) FROM {table_name}) > 0
            )
            """,
        )


def migrate(sqlite_path, postgres_url):
    """Run the SQLite-to-PostgreSQL copy and return table counts."""
    validate_database_config(database_type="postgres", database_url=postgres_url)
    sqlite_connection = get_connection(sqlite_path, database_type="sqlite")
    postgres_connection = get_connection(
        database_type="postgres",
        database_url=postgres_url,
    )

    try:
        initialize_database(postgres_connection)
        summary = {}

        with postgres_connection:
            for table in TABLES:
                rows = fetch_rows(sqlite_connection, table)
                inserted = insert_rows(postgres_connection, table, rows)
                summary[table["name"]] = {
                    "sqlite_count": len(rows),
                    "postgres_inserted": inserted,
                }
            reset_identity_sequences(postgres_connection)

        for table in TABLES:
            table_name = table["name"]
            summary[table_name]["postgres_count"] = count_rows(
                postgres_connection,
                table_name,
            )

        return summary
    finally:
        sqlite_connection.close()
        postgres_connection.close()


def verify_counts(summary):
    """Raise when PostgreSQL row counts do not match SQLite source counts."""
    mismatches = []
    for table_name, table_summary in summary.items():
        if table_summary["sqlite_count"] != table_summary["postgres_count"]:
            mismatches.append(
                f"{table_name}: sqlite={table_summary['sqlite_count']} "
                f"postgres={table_summary['postgres_count']}"
            )

    if mismatches:
        raise RuntimeError("Row count verification failed: " + "; ".join(mismatches))


def print_summary(summary):
    """Print migration counts for each table."""
    print("SQLite to PostgreSQL migration summary")
    print("-------------------------------------")
    for table_name, table_summary in summary.items():
        print(
            f"{table_name}: sqlite={table_summary['sqlite_count']}, "
            f"inserted={table_summary['postgres_inserted']}, "
            f"postgres={table_summary['postgres_count']}"
        )


def main():
    """Run the migration utility."""
    args = parse_args()
    try:
        summary = migrate(args.sqlite, args.postgres_url)
        verify_counts(summary)
    except Exception as error:
        logger.error(error)
        print(error)
        return 1

    print_summary(summary)
    print("Row count verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

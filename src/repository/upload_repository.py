"""SQLite repository helpers for uploaded datasets."""

from datetime import datetime, timezone

try:
    from src.config import DATABASE_PATH
    from src.database import get_connection
except ImportError:
    from config import DATABASE_PATH
    from database import get_connection


def initialize_upload_table(connection):
    """Create the uploads table if it does not exist."""
    connection.execute(
        """
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
    )
    connection.commit()


def _row_to_dict(row):
    """Convert a SQLite upload row into a dictionary."""
    if row is None:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "filename": row[2],
        "rows_processed": row[3],
        "products_added": row[4],
        "reviews_added": row[5],
        "duplicates_skipped": row[6],
        "uploaded_at": row[7],
    }


def _get_connection(db_path=DATABASE_PATH):
    """Open the database and ensure the uploads table exists."""
    connection = get_connection(db_path)
    initialize_upload_table(connection)
    return connection


def create_upload_record(
    user_id,
    filename,
    rows_processed,
    products_added,
    reviews_added,
    duplicates_skipped,
    db_path=DATABASE_PATH,
):
    """Create an upload metadata record and return it."""
    uploaded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO uploads (
                user_id,
                filename,
                rows_processed,
                products_added,
                reviews_added,
                duplicates_skipped,
                uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                filename,
                rows_processed,
                products_added,
                reviews_added,
                duplicates_skipped,
                uploaded_at,
            ),
        )
        upload_id = cursor.lastrowid

    return get_upload_by_id(upload_id, user_id=user_id, db_path=db_path)


def get_upload_history(user_id, db_path=DATABASE_PATH):
    """Return upload records for one user, newest first."""
    with _get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                rows_processed,
                products_added,
                reviews_added,
                duplicates_skipped,
                uploaded_at
            FROM uploads
            WHERE user_id = ?
            ORDER BY uploaded_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_upload_by_id(upload_id, user_id, db_path=DATABASE_PATH):
    """Return one upload record for a user or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                rows_processed,
                products_added,
                reviews_added,
                duplicates_skipped,
                uploaded_at
            FROM uploads
            WHERE id = ? AND user_id = ?
            """,
            (upload_id, user_id),
        ).fetchone()

    return _row_to_dict(row)

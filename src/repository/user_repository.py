"""SQLite repository helpers for MarketMind users."""

from datetime import datetime, timezone
import sqlite3

try:
    from src.config import DATABASE_PATH
    from src.database import get_connection
except ImportError:
    from config import DATABASE_PATH
    from database import get_connection


def initialize_user_table(connection):
    """Create the users table if it does not exist."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def _row_to_dict(row):
    """Convert a SQLite user row into a dictionary."""
    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
        "created_at": row[4],
    }


def _get_connection(db_path=DATABASE_PATH):
    """Open the database and ensure the users table exists."""
    connection = get_connection(db_path)
    initialize_user_table(connection)
    return connection


def create_user(username, email, password_hash, db_path=DATABASE_PATH):
    """Create a user row and return it as a dictionary."""
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _get_connection(db_path) as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, created_at),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Username or email already exists.") from error

        user_id = cursor.lastrowid
        return get_user_by_id(user_id, db_path=db_path)


def get_user_by_id(user_id, db_path=DATABASE_PATH):
    """Return one user by ID or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return _row_to_dict(row)


def get_user_by_email(email, db_path=DATABASE_PATH):
    """Return one user by email or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    return _row_to_dict(row)


def get_user_by_username(username, db_path=DATABASE_PATH):
    """Return one user by username or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    return _row_to_dict(row)

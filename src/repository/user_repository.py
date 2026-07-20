"""Repository helpers for MarketMind users."""

from datetime import datetime, timezone

try:
    from src.config import DATABASE_PATH
    from src.database import (
        execute,
        get_connection,
        initialize_database,
        is_integrity_error,
        is_postgres_connection,
    )
except ImportError:
    from config import DATABASE_PATH
    from database import (
        execute,
        get_connection,
        initialize_database,
        is_integrity_error,
        is_postgres_connection,
    )


USER_SELECT_SQL = """
    SELECT id, username, email, password_hash, created_at
    FROM users
"""


def initialize_user_table(connection):
    """Create the users table if it does not exist."""
    initialize_database(connection)


def _row_to_dict(row):
    """Convert a database user row into a dictionary."""
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
            insert_sql = """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """
            if is_postgres_connection(connection):
                insert_sql += " RETURNING id"

            cursor = execute(
                connection,
                insert_sql,
                (username, email, password_hash, created_at),
            )
            if is_postgres_connection(connection):
                user_id = cursor.fetchone()[0]
            else:
                user_id = cursor.lastrowid
        except Exception as error:
            if is_integrity_error(error):
                raise ValueError("Username or email already exists.") from error
            raise

        return get_user_by_id(user_id, db_path=db_path)


def get_user_by_id(user_id, db_path=DATABASE_PATH):
    """Return one user by ID or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = execute(
            connection,
            USER_SELECT_SQL
            + """
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    return _row_to_dict(row)


def get_user_by_email(email, db_path=DATABASE_PATH):
    """Return one user by email or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = execute(
            connection,
            USER_SELECT_SQL
            + """
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    return _row_to_dict(row)


def get_user_by_username(username, db_path=DATABASE_PATH):
    """Return one user by username or None when it does not exist."""
    with _get_connection(db_path) as connection:
        row = execute(
            connection,
            USER_SELECT_SQL
            + """
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    return _row_to_dict(row)

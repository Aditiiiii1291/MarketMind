"""Database connection abstraction for SQLite and PostgreSQL."""

import sqlite3
from pathlib import Path

import pandas as pd

try:
    from src import config
    from src.utils.file_io import ensure_parent_dir
except ImportError:
    import config
    from utils.file_io import ensure_parent_dir


SQLITE = "sqlite"
POSTGRES = "postgres"
SUPPORTED_DATABASE_TYPES = {SQLITE, POSTGRES}
POSTGRES_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "sql" / "postgres_schema.sql"


class DatabaseConfigurationError(RuntimeError):
    """Raised when database configuration is invalid for the selected backend."""


class DatabaseConnection:
    """Small DB-API adapter that hides SQL placeholder differences."""

    def __init__(self, raw_connection, database_type):
        self.raw_connection = raw_connection
        self.database_type = normalize_database_type(database_type)

    def execute(self, sql, params=None):
        """Execute SQL using the active database's parameter style."""
        prepared_sql = prepare_sql(sql, self.database_type)
        if params is None:
            return self.raw_connection.execute(prepared_sql)

        return self.raw_connection.execute(prepared_sql, params)

    def executemany(self, sql, params_seq):
        """Execute one SQL statement for many parameter sets."""
        return self.raw_connection.executemany(
            prepare_sql(sql, self.database_type),
            params_seq,
        )

    def commit(self):
        """Commit the active transaction."""
        return self.raw_connection.commit()

    def rollback(self):
        """Roll back the active transaction."""
        return self.raw_connection.rollback()

    def close(self):
        """Close the underlying database connection."""
        return self.raw_connection.close()

    def cursor(self):
        """Return a raw DB-API cursor."""
        return self.raw_connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False


def normalize_database_type(database_type):
    """Normalize and validate a configured database type."""
    normalized = str(database_type or SQLITE).strip().lower()
    if normalized == "postgresql":
        normalized = POSTGRES
    if normalized not in SUPPORTED_DATABASE_TYPES:
        raise DatabaseConfigurationError(
            "Unsupported MARKETMIND_DATABASE_TYPE. "
            "Expected 'sqlite' or 'postgres'."
        )

    return normalized


def get_database_type(database_type=None):
    """Return the active configured database type."""
    if database_type is None:
        database_type = config.DATABASE_TYPE

    return normalize_database_type(database_type)


def validate_database_config(database_type=None, database_url=None):
    """Validate configured database settings and raise friendly errors."""
    active_type = get_database_type(database_type)
    if active_type == SQLITE:
        return active_type

    if database_url is None:
        database_url = config.DATABASE_URL
    if str(database_url or "").strip() == "":
        raise DatabaseConfigurationError(
            "MARKETMIND_DATABASE_URL is required when "
            "MARKETMIND_DATABASE_TYPE=postgres."
        )

    _import_psycopg()
    return active_type


def get_connection(db_path=None, database_type=None, database_url=None):
    """Open a database connection for the configured backend."""
    active_type = validate_database_config(database_type, database_url)

    if active_type == SQLITE:
        if db_path is None:
            db_path = config.DATABASE_PATH
        if str(db_path) != ":memory:":
            db_path = ensure_parent_dir(db_path)
        raw_connection = sqlite3.connect(db_path)
        raw_connection.execute("PRAGMA foreign_keys = ON")
        return DatabaseConnection(raw_connection, SQLITE)

    psycopg = _import_psycopg()
    if database_url is None:
        database_url = config.DATABASE_URL
    raw_connection = psycopg.connect(database_url)
    return DatabaseConnection(raw_connection, POSTGRES)


def prepare_sql(sql, database_type):
    """Convert repository SQL into the active backend's parameter style."""
    if normalize_database_type(database_type) == POSTGRES:
        return _replace_qmark_placeholders(str(sql))

    return sql


def execute(connection, sql, params=None):
    """Execute SQL through a wrapped or raw connection."""
    if isinstance(connection, DatabaseConnection):
        return connection.execute(sql, params)

    database_type = get_connection_type(connection)
    prepared_sql = prepare_sql(sql, database_type)
    if params is None:
        return connection.execute(prepared_sql)

    return connection.execute(prepared_sql, params)


def read_sql_query(sql, connection, params=None):
    """Return query results as a DataFrame for SQLite or PostgreSQL."""
    database_type = get_connection_type(connection)
    if database_type == SQLITE:
        raw_connection = unwrap_connection(connection)
        return pd.read_sql_query(sql, raw_connection, params=params)

    cursor = execute(connection, sql, params)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def is_sqlite_connection(connection):
    """Return True for wrapped or raw SQLite connections."""
    return get_connection_type(connection) == SQLITE


def is_postgres_connection(connection):
    """Return True for wrapped or raw PostgreSQL connections."""
    return get_connection_type(connection) == POSTGRES


def get_connection_type(connection):
    """Infer the database type from a wrapped or raw connection object."""
    if isinstance(connection, DatabaseConnection):
        return connection.database_type
    if isinstance(connection, sqlite3.Connection):
        return SQLITE

    module_name = connection.__class__.__module__.lower()
    if "psycopg" in module_name:
        return POSTGRES

    return get_database_type()


def unwrap_connection(connection):
    """Return the underlying DB-API connection."""
    if isinstance(connection, DatabaseConnection):
        return connection.raw_connection

    return connection


def is_integrity_error(error):
    """Return True when an exception represents a database integrity error."""
    if isinstance(error, sqlite3.IntegrityError):
        return True

    module_name = error.__class__.__module__.lower()
    sqlstate = getattr(error, "sqlstate", "")
    return "psycopg" in module_name and str(sqlstate).startswith("23")


def initialize_postgres_schema(connection):
    """Initialize PostgreSQL tables and indexes from the SQL schema script."""
    if not POSTGRES_SCHEMA_PATH.exists():
        raise DatabaseConfigurationError(
            f"PostgreSQL schema file not found: {POSTGRES_SCHEMA_PATH}"
        )

    schema_sql = POSTGRES_SCHEMA_PATH.read_text(encoding="utf-8")
    for statement in _split_sql_statements(schema_sql):
        execute(connection, statement)
    connection.commit()


def _replace_qmark_placeholders(sql):
    """Replace unquoted '?' placeholders with psycopg '%s' placeholders."""
    output = []
    in_single_quote = False
    in_double_quote = False
    index = 0

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if char == "'" and not in_double_quote:
            output.append(char)
            if in_single_quote and next_char == "'":
                output.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            output.append(char)
            in_double_quote = not in_double_quote
        elif char == "?" and not in_single_quote and not in_double_quote:
            output.append("%s")
        else:
            output.append(char)

        index += 1

    return "".join(output)


def _split_sql_statements(sql):
    """Split a simple SQL script into executable statements."""
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False

    for char in sql:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote

        if char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return statements


def _import_psycopg():
    """Import psycopg lazily so SQLite mode has no PostgreSQL runtime cost."""
    try:
        import psycopg
    except ImportError as error:
        raise DatabaseConfigurationError(
            "PostgreSQL support requires the 'psycopg[binary]' dependency. "
            "Install requirements.txt before using MARKETMIND_DATABASE_TYPE=postgres."
        ) from error

    return psycopg

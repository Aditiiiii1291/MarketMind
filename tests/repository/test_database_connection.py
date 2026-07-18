"""Tests for database connection configuration helpers."""

import pytest


def test_sqlite_connection_initializes_schema(tmp_path):
    """SQLite remains the default supported database backend."""
    from src.database import execute, get_connection, initialize_database

    db_path = tmp_path / "sqlite_default.db"
    connection = get_connection(db_path, database_type="sqlite")
    try:
        initialize_database(connection)
        source_count = execute(
            connection,
            "SELECT COUNT(*) FROM dataset_sources",
        ).fetchone()[0]
    finally:
        connection.close()

    assert source_count == 0


def test_postgres_requires_database_url():
    """PostgreSQL mode fails early with a friendly missing-URL error."""
    from src.database.connection import DatabaseConfigurationError
    from src.database.connection import validate_database_config

    with pytest.raises(DatabaseConfigurationError) as error:
        validate_database_config(database_type="postgres", database_url="")

    assert "MARKETMIND_DATABASE_URL is required" in str(error.value)


def test_postgres_placeholder_conversion_preserves_string_literals():
    """Repository SQL can use '?' placeholders across both database types."""
    from src.database.connection import prepare_sql

    sql = "SELECT ? AS value, '?' AS literal"

    assert prepare_sql(sql, "postgres") == "SELECT %s AS value, '?' AS literal"

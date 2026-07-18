"""Tests for upload metadata repository behavior."""


def test_upload_repository_create_read_and_history(temporary_database):
    """Upload records are persisted and scoped to the requesting user."""
    from src.repository import upload_repository

    first = upload_repository.create_upload_record(
        user_id=1,
        filename="first.csv",
        rows_processed=3,
        products_added=1,
        reviews_added=3,
        duplicates_skipped=0,
    )
    second = upload_repository.create_upload_record(
        user_id=1,
        filename="second.csv",
        rows_processed=2,
        products_added=0,
        reviews_added=1,
        duplicates_skipped=1,
    )
    other_user = upload_repository.create_upload_record(
        user_id=2,
        filename="other.csv",
        rows_processed=1,
        products_added=1,
        reviews_added=1,
        duplicates_skipped=0,
    )

    history = upload_repository.get_upload_history(1)

    assert [record["id"] for record in history] == [second["id"], first["id"]]
    assert upload_repository.get_upload_by_id(first["id"], 1)["filename"] == "first.csv"
    assert upload_repository.get_upload_by_id(other_user["id"], 1) is None

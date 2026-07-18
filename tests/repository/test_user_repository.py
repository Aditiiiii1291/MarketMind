"""Tests for user repository persistence behavior."""

import pytest


def test_user_repository_create_read_and_duplicate_handling(temporary_database):
    """Users can be created and fetched, while unique constraints are preserved."""
    from src.repository import user_repository

    created = user_repository.create_user(
        username="alice",
        email="alice@example.com",
        password_hash="hashed-password",
    )
    user = user_repository.get_user_by_email("alice@example.com")

    assert created is None
    assert user["id"] is not None
    assert user_repository.get_user_by_id(user["id"])["username"] == "alice"
    assert user_repository.get_user_by_email("alice@example.com")["id"] == user["id"]
    assert user_repository.get_user_by_username("alice")["email"] == "alice@example.com"

    with pytest.raises(ValueError):
        user_repository.create_user(
            username="alice",
            email="alice2@example.com",
            password_hash="hashed-password",
        )

    with pytest.raises(ValueError):
        user_repository.create_user(
            username="alice2",
            email="alice@example.com",
            password_hash="hashed-password",
        )


def test_user_repository_returns_none_for_missing_user(temporary_database):
    """Missing user lookups return None instead of raising."""
    from src.repository import user_repository

    assert user_repository.get_user_by_id(9999) is None
    assert user_repository.get_user_by_email("missing@example.com") is None
    assert user_repository.get_user_by_username("missing") is None

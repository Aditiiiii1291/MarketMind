"""Authentication API tests."""

from datetime import timedelta


def test_register_login_and_get_current_user(client):
    """A user can register, log in, and call /auth/me."""
    register = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "Password123",
        },
    )
    login = client.post(
        "/auth/login",
        json={"username_or_email": "alice@example.com", "password": "Password123"},
    )
    token = login.json()["access_token"]
    current_user = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert register.status_code == 201
    assert register.json() is None
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert current_user.status_code == 200
    assert current_user.json()["username"] == "alice"


def test_duplicate_email_and_username_are_rejected(client):
    """Registration preserves current duplicate validation behavior."""
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Password123",
    }
    assert client.post("/auth/register", json=payload).status_code == 201

    duplicate_email = client.post(
        "/auth/register",
        json={**payload, "username": "alice2"},
    )
    duplicate_username = client.post(
        "/auth/register",
        json={**payload, "email": "alice2@example.com"},
    )

    assert duplicate_email.status_code == 400
    assert duplicate_email.json()["detail"] == "Email is already registered."
    assert duplicate_username.status_code == 400
    assert duplicate_username.json()["detail"] == "Username is already registered."


def test_invalid_password_and_credentials_are_rejected(client):
    """Short passwords and wrong login credentials fail with current statuses."""
    weak_password = client.post(
        "/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "short"},
    )
    client.post(
        "/auth/register",
        json={
            "username": "carol",
            "email": "carol@example.com",
            "password": "Password123",
        },
    )
    wrong_password = client.post(
        "/auth/login",
        json={"username_or_email": "carol", "password": "wrong-password"},
    )

    assert weak_password.status_code == 400
    assert weak_password.json()["detail"] == "Password must be at least 8 characters long."
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid credentials."


def test_invalid_and_expired_jwt_are_rejected(client):
    """JWT verification rejects malformed and expired bearer tokens."""
    from api.auth.security import create_access_token

    register = client.post(
        "/auth/register",
        json={
            "username": "dave",
            "email": "dave@example.com",
            "password": "Password123",
        },
    )
    from src.repository import user_repository

    user = user_repository.get_user_by_username("dave")
    expired_token = create_access_token(
        user["id"],
        expires_delta=timedelta(minutes=-1),
    )

    assert register.status_code == 201
    invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    expired = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid or expired token."
    assert expired.status_code == 401
    assert expired.json()["detail"] == "Invalid or expired token."


def test_protected_endpoint_requires_authentication(client):
    """Protected routers continue to require bearer credentials."""
    response = client.get("/dashboard")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."

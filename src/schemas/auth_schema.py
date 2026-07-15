"""Authentication service dataclasses."""

from dataclasses import dataclass


@dataclass
class UserCreate:
    """Request data for registering a new user."""

    username: str
    email: str
    password: str


@dataclass
class UserLogin:
    """Request data for authenticating a user."""

    username_or_email: str
    password: str


@dataclass
class UserResponse:
    """Public user data returned by authentication services."""

    id: int
    username: str
    email: str
    created_at: str


@dataclass
class TokenResponse:
    """Access token response returned after successful authentication."""

    access_token: str
    token_type: str
    expires_in_minutes: int

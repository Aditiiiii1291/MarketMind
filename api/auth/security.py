"""Password hashing and JWT security helpers for MarketMind API."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

try:
    from src.config import (
        ACCESS_TOKEN_EXPIRE_MINUTES,
        JWT_ALGORITHM,
        JWT_SECRET_KEY,
    )
    from src.services import user_service
except ImportError:
    from config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY
    from services import user_service


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password):
    """Hash a plaintext password for storage."""
    return password_context.hash(password)


def verify_password(password, password_hash):
    """Return True when a plaintext password matches a stored hash."""
    return password_context.verify(password, password_hash)


def create_access_token(user_id, expires_delta=None):
    """Create a signed JWT access token for a user ID."""
    expire_delta = expires_delta
    if expire_delta is None:
        expire_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expires_at = datetime.now(timezone.utc) + expire_delta
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_access_token(token):
    """Verify a JWT access token and return the encoded user ID."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError("Token subject is missing.")
        return int(user_id)
    except (JWTError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Return the current authenticated user from a bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_access_token(credentials.credentials)
    user = user_service.fetch_current_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

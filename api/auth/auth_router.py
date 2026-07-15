"""Authentication API routes for MarketMind."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from api.routers import to_jsonable
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.schemas.auth_schema import TokenResponse, UserCreate, UserLogin
from src.services import user_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a new API user with a hashed password.",
    response_description="Public user profile for the created user.",
)
def register_user(user_create: UserCreate):
    """Register a new user account."""
    try:
        user = user_service.register_user(user_create, hash_password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return to_jsonable(user)


@router.post(
    "/login",
    summary="Login user",
    description="Authenticate a user and return a JWT bearer token.",
    response_description="JWT access token response.",
)
def login_user(user_login: UserLogin):
    """Authenticate user credentials and return an access token."""
    try:
        user = user_service.authenticate_credentials(user_login, verify_password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(user.id)
    return to_jsonable(
        TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
    )


@router.get(
    "/me",
    summary="Get current user",
    description="Return the current authenticated user from a JWT bearer token.",
    response_description="Public current-user profile.",
)
def get_me(current_user=Depends(get_current_user)):
    """Return the authenticated current user."""
    return to_jsonable(current_user)

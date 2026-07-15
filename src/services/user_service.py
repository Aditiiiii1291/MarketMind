"""User service functions for authentication workflows."""

try:
    from src.repository import user_repository
    from src.schemas.auth_schema import UserResponse
except ImportError:
    from repository import user_repository
    from schemas.auth_schema import UserResponse


def _clean_username(username):
    """Normalize username input for validation and storage."""
    return str(username or "").strip()


def _clean_email(email):
    """Normalize email input for validation and storage."""
    return str(email or "").strip().lower()


def _to_user_response(user_record):
    """Convert a repository user record into a public user response."""
    if user_record is None:
        return None

    return UserResponse(
        id=user_record["id"],
        username=user_record["username"],
        email=user_record["email"],
        created_at=user_record["created_at"],
    )


def validate_email_uniqueness(email):
    """Raise ValueError when an email is already registered."""
    if user_repository.get_user_by_email(email) is not None:
        raise ValueError("Email is already registered.")


def validate_username_uniqueness(username):
    """Raise ValueError when a username is already registered."""
    if user_repository.get_user_by_username(username) is not None:
        raise ValueError("Username is already registered.")


def validate_password_strength(password):
    """Raise ValueError when a password does not meet minimum strength rules."""
    if len(str(password or "")) < 8:
        raise ValueError("Password must be at least 8 characters long.")


def register_user(user_create, password_hasher):
    """Register a new user after validating uniqueness and password strength."""
    username = _clean_username(user_create.username)
    email = _clean_email(user_create.email)
    password = str(user_create.password or "")

    if username == "":
        raise ValueError("Username is required.")
    if email == "" or "@" not in email:
        raise ValueError("A valid email is required.")

    validate_password_strength(password)
    validate_username_uniqueness(username)
    validate_email_uniqueness(email)

    password_hash = password_hasher(password)
    user_record = user_repository.create_user(
        username=username,
        email=email,
        password_hash=password_hash,
    )

    return _to_user_response(user_record)


def authenticate_credentials(user_login, password_verifier):
    """Authenticate a username/email and password pair."""
    username_or_email = str(user_login.username_or_email or "").strip()
    password = str(user_login.password or "")

    if username_or_email == "" or password == "":
        raise ValueError("Username/email and password are required.")

    if "@" in username_or_email:
        user_record = user_repository.get_user_by_email(
            _clean_email(username_or_email)
        )
    else:
        user_record = user_repository.get_user_by_username(
            _clean_username(username_or_email)
        )

    if user_record is None:
        return None
    if not password_verifier(password, user_record["password_hash"]):
        return None

    return _to_user_response(user_record)


def fetch_current_user(user_id):
    """Return the public current-user response for a verified user ID."""
    user_record = user_repository.get_user_by_id(user_id)
    return _to_user_response(user_record)

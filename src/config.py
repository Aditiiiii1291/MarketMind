"""Central configuration values for MarketMind paths and environment settings."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE_PATH)


def get_env(name, default=None):
    """Return a string environment value with a default fallback."""
    return os.getenv(name, default)


def require_env(name):
    """Return a required environment value or raise a clear configuration error."""
    value = get_env(name)
    if value is None or value == "":
        raise RuntimeError(f"Required environment variable is missing: {name}")

    return value


def get_int_env(name, default):
    """Return an integer environment value with a default fallback."""
    try:
        return int(get_env(name, str(default)))
    except ValueError:
        return default


def get_path_env(name, default):
    """Return a resolved path from an environment value or default path."""
    raw_path = Path(get_env(name, str(default)))
    if raw_path.is_absolute():
        return raw_path

    return PROJECT_ROOT / raw_path


def get_database_path():
    """Return the configured SQLite database path."""
    return get_path_env(
        "MARKETMIND_DATABASE_PATH",
        PROJECT_ROOT / "data" / "marketmind.db",
    )


def get_reports_path():
    """Return the configured reports directory path."""
    return get_path_env("MARKETMIND_REPORT_DIR", PROJECT_ROOT / "reports")


def _warn_missing_optional(name):
    """Print a friendly warning when an optional variable is not configured."""
    if not get_env(name):
        print(f"Warning: optional environment variable {name} is not configured.")


def validate_database_settings(database_type=None, database_url=None):
    """Validate database configuration without opening a database connection."""
    if database_type is None:
        database_type = DATABASE_TYPE
    if database_url is None:
        database_url = DATABASE_URL

    normalized_type = str(database_type or "sqlite").strip().lower()
    if normalized_type == "postgresql":
        normalized_type = "postgres"

    if normalized_type not in {"sqlite", "postgres"}:
        raise RuntimeError(
            "Unsupported MARKETMIND_DATABASE_TYPE. "
            "Expected 'sqlite' or 'postgres'."
        )
    if normalized_type == "postgres" and str(database_url or "").strip() == "":
        raise RuntimeError(
            "MARKETMIND_DATABASE_URL is required when "
            "MARKETMIND_DATABASE_TYPE=postgres."
        )

    return normalized_type


APP_ENV = get_env("MARKETMIND_ENV", "development")

DATA_DIR = get_path_env("MARKETMIND_DATA_DIR", PROJECT_ROOT / "data")
RAW_DATA_DIR = get_path_env("MARKETMIND_RAW_DATA_DIR", DATA_DIR / "raw")
PROCESSED_DATA_DIR = get_path_env(
    "MARKETMIND_PROCESSED_DATA_DIR",
    DATA_DIR / "processed",
)
REPORTS_DIR = get_reports_path()
MODELS_DIR = get_path_env("MARKETMIND_MODEL_DIR", PROJECT_ROOT / "models")

DATABASE_TYPE = get_env("MARKETMIND_DATABASE_TYPE", "sqlite")
DATABASE_URL = get_env("MARKETMIND_DATABASE_URL", "")
DATABASE_PATH = get_database_path()
RAW_REVIEWS_PATH = get_path_env(
    "MARKETMIND_RAW_REVIEWS_PATH",
    RAW_DATA_DIR / "Equal.csv",
)
MINI_ELECTRONICS_REVIEWS_PATH = get_path_env(
    "MARKETMIND_MINI_ELECTRONICS_REVIEWS_PATH",
    RAW_DATA_DIR / "mini_electronics_reviews.csv",
)
PROCESSED_REVIEWS_PATH = get_path_env(
    "MARKETMIND_PROCESSED_REVIEWS_PATH",
    PROCESSED_DATA_DIR / "marketmind_clean_reviews.csv",
)

SENTIMENT_MODEL_PATH = get_path_env(
    "MARKETMIND_SENTIMENT_MODEL_PATH",
    MODELS_DIR / "sentiment_model.pkl",
)
TFIDF_VECTORIZER_PATH = get_path_env(
    "MARKETMIND_TFIDF_VECTORIZER_PATH",
    MODELS_DIR / "tfidf_vectorizer.pkl",
)

TOP_COMPLAINTS_REPORT_PATH = get_path_env(
    "MARKETMIND_TOP_COMPLAINTS_REPORT_PATH",
    REPORTS_DIR / "top_complaints.csv",
)
COMPLAINT_CATEGORY_SUMMARY_PATH = get_path_env(
    "MARKETMIND_COMPLAINT_CATEGORY_SUMMARY_PATH",
    REPORTS_DIR / "complaint_category_summary.csv",
)
REVIEW_PERSONAS_REPORT_PATH = get_path_env(
    "MARKETMIND_REVIEW_PERSONAS_REPORT_PATH",
    REPORTS_DIR / "review_personas.csv",
)
PERSONA_PROFILES_REPORT_PATH = get_path_env(
    "MARKETMIND_PERSONA_PROFILES_REPORT_PATH",
    REPORTS_DIR / "persona_profiles.csv",
)
PRODUCT_HEALTH_REPORT_PATH = get_path_env(
    "MARKETMIND_PRODUCT_HEALTH_REPORT_PATH",
    REPORTS_DIR / "product_health_score.csv",
)
PRODUCT_COMPARISON_REPORT_PATH = get_path_env(
    "MARKETMIND_PRODUCT_COMPARISON_REPORT_PATH",
    REPORTS_DIR / "product_comparison.csv",
)
CONCEPT_SIMULATION_REPORT_PATH = get_path_env(
    "MARKETMIND_CONCEPT_SIMULATION_REPORT_PATH",
    REPORTS_DIR / "concept_simulation.csv",
)

UPLOADS_DIR = get_path_env("MARKETMIND_UPLOAD_DIR", DATA_DIR / "uploads")
UPLOAD_MAX_SIZE_BYTES = get_int_env("MARKETMIND_UPLOAD_MAX_SIZE_BYTES", 5242880)

JWT_SECRET_KEY = get_env("MARKETMIND_JWT_SECRET_KEY", "marketmind-dev-secret")
JWT_ALGORITHM = get_env("MARKETMIND_JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = get_int_env("MARKETMIND_ACCESS_TOKEN_EXPIRE_MINUTES", 60)

OPENAI_API_KEY = get_env("OPENAI_API_KEY", "")
OPENAI_MODEL = get_env("OPENAI_MODEL", "gpt-4.1-mini")

GOOGLE_API_KEY = get_env("GOOGLE_API_KEY", "")
GOOGLE_MODEL = get_env("GOOGLE_MODEL", "gemini-2.5-flash")

_warn_missing_optional("OPENAI_API_KEY")
_warn_missing_optional("OPENAI_MODEL")

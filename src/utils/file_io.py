"""Small file and CSV helpers shared by MarketMind modules."""

from pathlib import Path

import pandas as pd

try:
    from src.config import PROJECT_ROOT
except ImportError:
    from config import PROJECT_ROOT


def resolve_project_path(file_path):
    """Resolve project-relative paths while preserving absolute paths."""
    path = Path(file_path)
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def display_path(file_path):
    """Return a readable path, relative to the project root when possible."""
    path = resolve_project_path(file_path)
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def ensure_parent_dir(file_path):
    """Create a file's parent directory and return the resolved path."""
    path = resolve_project_path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def require_file(file_path, description="File"):
    """Return a resolved file path or raise a clear missing-file error."""
    path = resolve_project_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {display_path(path)}")

    return path


def load_csv(file_path, description="CSV file", **read_csv_kwargs):
    """Load a CSV after validating that it exists."""
    path = require_file(file_path, description)
    return pd.read_csv(path, **read_csv_kwargs)

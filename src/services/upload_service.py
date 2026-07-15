"""Upload service for dataset ingestion workflows."""

from pathlib import Path
import re

import pandas as pd

try:
    from scripts import ingest_dataset
    from src.config import DATABASE_PATH, UPLOAD_MAX_SIZE_BYTES, UPLOADS_DIR
    from src.repository import upload_repository
    from src.schemas.upload_schema import (
        UploadHistory,
        UploadHistoryItem,
        UploadResult,
        UploadSummary,
    )
    from src.utils.file_io import ensure_parent_dir
except ImportError:
    from scripts import ingest_dataset
    from config import DATABASE_PATH, UPLOAD_MAX_SIZE_BYTES, UPLOADS_DIR
    from repository import upload_repository
    from schemas.upload_schema import (
        UploadHistory,
        UploadHistoryItem,
        UploadResult,
        UploadSummary,
    )
    from utils.file_io import ensure_parent_dir


DEFAULT_UPLOAD_CATEGORY = "Electronics"


def _validate_csv_upload(filename, content):
    """Validate upload filename, size, and basic content."""
    if not str(filename or "").lower().endswith(".csv"):
        raise ValueError("Only CSV uploads are supported.")

    if len(content) == 0:
        raise ValueError("Uploaded CSV is empty.")

    if len(content) > UPLOAD_MAX_SIZE_BYTES:
        raise ValueError("Uploaded CSV exceeds the configured size limit.")


def _sanitize_source_part(value):
    """Return a stable source-name component from upload metadata."""
    source_part = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().lower())
    source_part = source_part.strip("_")

    return source_part or "upload"


def _build_source_name(user_id, filename):
    """Build a stable ingestion source name for duplicate detection."""
    stem = Path(filename).stem
    return f"upload_user_{user_id}_{_sanitize_source_part(stem)}"


def _build_temp_upload_path(user_id, filename):
    """Build the temporary file path used by the ingestion pipeline."""
    safe_filename = _sanitize_source_part(Path(filename).stem) + ".csv"
    return UPLOADS_DIR / str(user_id) / safe_filename


def _to_history_item(upload_record):
    """Convert an upload repository row into an UploadHistoryItem."""
    return UploadHistoryItem(
        id=upload_record["id"],
        user_id=upload_record["user_id"],
        filename=upload_record["filename"],
        rows_processed=upload_record["rows_processed"],
        products_added=upload_record["products_added"],
        reviews_added=upload_record["reviews_added"],
        duplicates_skipped=upload_record["duplicates_skipped"],
        uploaded_at=upload_record["uploaded_at"],
    )


def save_uploaded_dataset(filename, content, user_id, category=DEFAULT_UPLOAD_CATEGORY):
    """Validate, save, ingest, and record an uploaded review CSV."""
    _validate_csv_upload(filename, content)

    upload_path = ensure_parent_dir(_build_temp_upload_path(user_id, filename))
    upload_path.write_bytes(content)
    source_name = _build_source_name(user_id, filename)

    try:
        raw_df = ingest_dataset.read_external_csv(upload_path)
    except pd.errors.EmptyDataError as error:
        raise ValueError("Uploaded CSV is empty.") from error
    except pd.errors.ParserError as error:
        raise ValueError("Uploaded CSV could not be parsed.") from error
    except UnicodeDecodeError as error:
        raise ValueError("Uploaded CSV could not be decoded.") from error

    if raw_df.empty:
        raise ValueError("Uploaded CSV is empty.")

    if not ingest_dataset.validate_raw_columns(raw_df):
        raise ValueError(
            "Uploaded CSV is missing required columns or contains unexpected columns."
        )

    converted_df = ingest_dataset.convert_to_marketmind_schema(raw_df, category)
    valid_df, invalid_count = ingest_dataset.validate_converted_rows(converted_df)
    if valid_df.empty:
        raise ValueError("Uploaded CSV does not contain any valid review rows.")

    import_summary = ingest_dataset.import_rows(
        valid_df,
        DATABASE_PATH,
        source_name,
        str(upload_path),
    )
    rows_processed = len(valid_df)
    products_added = import_summary["products_inserted"]
    reviews_added = import_summary["reviews_inserted"]
    duplicates_skipped = import_summary["reviews_skipped_duplicates"]

    upload_record = upload_repository.create_upload_record(
        user_id=user_id,
        filename=filename,
        rows_processed=rows_processed,
        products_added=products_added,
        reviews_added=reviews_added,
        duplicates_skipped=duplicates_skipped,
    )
    history_item = _to_history_item(upload_record)

    return UploadResult(
        upload=history_item,
        summary=UploadSummary(
            rows_processed=rows_processed,
            products_added=products_added,
            reviews_added=reviews_added,
            duplicates_skipped=duplicates_skipped,
            invalid_rows=invalid_count,
        ),
        source_name=source_name,
    )


def get_upload_history(user_id):
    """Return upload history for one authenticated user."""
    uploads = [
        _to_history_item(upload_record)
        for upload_record in upload_repository.get_upload_history(user_id)
    ]
    return UploadHistory(uploads=uploads)


def get_upload_detail(upload_id, user_id):
    """Return one upload history item for an authenticated user."""
    upload_record = upload_repository.get_upload_by_id(upload_id, user_id)
    if upload_record is None:
        return None

    return _to_history_item(upload_record)

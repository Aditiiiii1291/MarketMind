"""Upload service dataclasses."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class UploadSummary:
    """Upload ingestion statistics for one dataset."""

    rows_processed: int
    products_added: int
    reviews_added: int
    duplicates_skipped: int
    invalid_rows: int


@dataclass
class UploadHistoryItem:
    """Upload metadata returned for history and detail views."""

    id: int
    user_id: int
    filename: str
    rows_processed: int
    products_added: int
    reviews_added: int
    duplicates_skipped: int
    uploaded_at: str


@dataclass
class UploadHistory:
    """Collection of upload history records for one user."""

    uploads: List[UploadHistoryItem] = field(default_factory=list)


@dataclass
class UploadResult:
    """Response returned after a successful upload ingestion."""

    upload: UploadHistoryItem
    summary: UploadSummary
    source_name: str

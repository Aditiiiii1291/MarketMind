"""Tests for duplicate review handling during SQLite ingestion."""

import pandas as pd


def test_ingest_import_rows_skips_duplicate_reviews(temporary_database):
    """Duplicate external rows are ignored by the existing review identity logic."""
    from scripts import ingest_dataset

    valid_df = pd.DataFrame(
        [
            {
                "product_name": "Duplicate Probe",
                "clean_price": 12.5,
                "rating": 5.0,
                "full_review": "Works well.",
                "cleaned_review": "works well",
                "sentiment": "positive",
                "category": "Electronics",
            },
            {
                "product_name": "Duplicate Probe",
                "clean_price": 12.5,
                "rating": 5.0,
                "full_review": "Works well.",
                "cleaned_review": "works well",
                "sentiment": "positive",
                "category": "Electronics",
            },
        ]
    )

    first = ingest_dataset.import_rows(
        valid_df,
        temporary_database,
        "duplicate_probe",
        "pytest",
    )
    second = ingest_dataset.import_rows(
        valid_df,
        temporary_database,
        "duplicate_probe",
        "pytest",
    )

    assert first["reviews_inserted"] == 1
    assert first["reviews_skipped_duplicates"] == 1
    assert second["reviews_inserted"] == 0
    assert second["reviews_skipped_duplicates"] == 2

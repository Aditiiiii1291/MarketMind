"""Tests for SQLite-backed review repository queries."""


def test_review_repository_reads_seeded_reviews(temporary_database):
    """Review queries return CSV-compatible DataFrames from SQLite."""
    from src import review_repository

    all_reviews = review_repository.get_all_reviews()
    matched_products = review_repository.search_products("Alpha")
    _, alpha_reviews = review_repository.get_product_reviews_by_query("AWC-38")
    summary = review_repository.get_review_summary_by_product(
        matched_products["product_id"].tolist()
    )
    category_reviews = review_repository.get_category_reviews("Electronics")
    overview = review_repository.get_database_overview()

    assert len(all_reviews) == 9
    assert list(all_reviews.columns) == review_repository.REVIEW_COLUMNS
    assert matched_products.iloc[0]["product_name"] == "Alpha Charger AWC-38"
    assert len(alpha_reviews) == 6
    assert int(summary.iloc[0]["review_count"]) == 6
    assert len(category_reviews) == 9
    assert overview["total_products"] == 2
    assert overview["total_reviews"] == 9


def test_review_repository_returns_empty_frames_for_missing_inputs(temporary_database):
    """Missing searches and blank categories return predictable empty DataFrames."""
    from src import review_repository

    assert review_repository.search_products("").empty
    assert review_repository.get_reviews_for_product_ids([]).empty
    assert review_repository.get_category_reviews("").empty
    assert review_repository.get_review_summary_by_product([]).empty

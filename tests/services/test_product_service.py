"""Tests for product service DTO behavior."""


def test_analyze_product_returns_product_health_dto(temporary_database):
    """Product analysis wraps the existing scoring engine result."""
    from src.services import product_service

    result = product_service.analyze_product("Alpha Charger")

    assert result.error is None
    assert result.product_query == "Alpha Charger"
    assert result.metrics["review_count"] == 6
    assert result.health_label == "Needs Improvement"
    assert result.category_summary is not None
    assert result.recommendations


def test_compare_products_returns_ranked_comparison(temporary_database):
    """Product comparison returns comparison tables and a readable insight."""
    from src.services import product_service

    result = product_service.compare_products(["Alpha Charger", "Beta Headphones"])

    assert result.comparison.shape[0] == 2
    assert result.ranked_products.iloc[0]["rank"] == 1
    assert "strongest product" in result.insight.lower()


def test_get_product_summary_preserves_compact_fields(temporary_database):
    """Product summaries keep the compact DTO contract."""
    from src.services import product_service

    health = product_service.get_product_health("Alpha Charger")
    summary = product_service.get_product_summary(health)

    assert summary.error is None
    assert summary.product_query == "Alpha Charger"
    assert summary.review_count == health.metrics["review_count"]
    assert summary.health_score == health.health_score


def test_product_summary_preserves_error_state(temporary_database):
    """Product summary DTOs preserve upstream analysis errors."""
    from src.services import product_service

    health = product_service.get_product_health("Missing Product")
    summary = product_service.get_product_summary(health)

    assert health.error is not None
    assert summary.error == health.error

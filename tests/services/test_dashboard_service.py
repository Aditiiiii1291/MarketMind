"""Tests for dashboard service response assembly."""


def test_dashboard_product_response_contains_metrics_and_tables(temporary_database):
    """Dashboard product analysis wraps product metrics and table inputs."""
    from src.services import dashboard_service

    response = dashboard_service.analyze_product_for_dashboard("Alpha Charger")

    assert response.error is None
    assert response.metrics.review_count == 6
    assert response.metrics.health_label == response.result.health_label
    assert response.tables.sentiment_distribution
    assert response.tables.matched_product_names == ["Alpha Charger AWC-38"]


def test_dashboard_concept_response_contains_launch_summary(
    test_vectorizer,
    sample_concept_payload,
):
    """Dashboard concept simulation wraps launch metrics and persona tables."""
    from src.services import dashboard_service

    response = dashboard_service.simulate_concept_for_dashboard(**sample_concept_payload)

    assert response.error is None
    assert response.metrics.launch_label == response.result.launch_label
    assert response.metrics.similar_review_count == response.result.similar_review_count
    assert len(response.tables.persona_simulations) == 3

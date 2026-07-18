"""Tests for concept service DTO behavior."""


def test_simulate_concept_returns_persona_results(test_vectorizer, sample_concept_payload):
    """Concept simulation returns launch and persona DTOs."""
    from src.services import concept_service

    result = concept_service.simulate_concept(**sample_concept_payload)

    assert result.error is None
    assert result.launch_label in {
        "Promising Concept",
        "Needs Refinement",
        "High Launch Risk",
    }
    assert len(result.persona_simulations) == 3
    assert len(result.recommendations) >= 2
    assert result.similar_review_count >= 0


def test_build_launch_summary_wraps_concept_result(test_vectorizer, sample_concept_payload):
    """Launch summary mirrors the key launch fields from a simulation."""
    from src.services import concept_service

    result = concept_service.simulate_concept(**sample_concept_payload)
    summary = concept_service.build_launch_summary(result)

    assert summary.error is None
    assert summary.launch_score == result.launch_score
    assert summary.launch_label == result.launch_label
    assert summary.similar_review_count == result.similar_review_count


def test_simulate_concept_validates_required_fields(test_vectorizer, sample_concept_payload):
    """Validation errors are preserved as ConceptSimulation error DTOs."""
    from src.services import concept_service

    payload = dict(sample_concept_payload)
    payload["product_name"] = ""
    result = concept_service.simulate_concept(**payload)

    assert result.error == "Please provide a non-empty product name."

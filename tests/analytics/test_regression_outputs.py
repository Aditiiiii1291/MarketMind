"""Regression tests for current analytics outputs from local artifacts."""

from pathlib import Path

import pytest


pytestmark = pytest.mark.regression


def _require_local_artifacts():
    """Skip regression tests when ignored local data/model artifacts are absent."""
    from src.config import DATABASE_PATH, TFIDF_VECTORIZER_PATH

    missing = [
        str(path)
        for path in (Path(DATABASE_PATH), Path(TFIDF_VECTORIZER_PATH))
        if not path.exists()
    ]
    if missing:
        pytest.skip("Local regression artifacts are not present: " + ", ".join(missing))


def test_awc38_product_health_regression():
    """Lock the current SQLite-backed AWC-38 product health baseline."""
    _require_local_artifacts()

    from src.services import product_service

    result = product_service.get_product_health("AWC-38")

    assert result.error is None
    assert result.metrics["review_count"] == 1847
    assert result.health_score == 20.35
    assert result.health_label == "Needs Improvement"


def test_concept_simulator_regression():
    """Lock the current concept simulation baseline from local artifacts."""
    _require_local_artifacts()

    from src.services import concept_service

    result = concept_service.simulate_concept(
        product_name="Smart Water Bottle",
        category="Electronics",
        price="999",
        features="USB charging, temperature display, hydration reminder",
        description="A smart bottle that tracks hydration and shows water temperature.",
    )

    assert result.error is None
    assert result.launch_score == 65.8
    assert result.launch_label == "Needs Refinement"
    assert len(result.persona_simulations) == 3
    assert len(result.recommendations) == 4

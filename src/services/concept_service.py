"""Concept simulation service functions for MarketMind workflows."""

try:
    from src.concept_simulator import simulate_product_concept
    from src.review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from src.schemas.concept_schema import (
        ConceptSimulation,
        LaunchSummary,
        PersonaSimulation,
    )
except ImportError:
    from concept_simulator import simulate_product_concept
    from review_repository import DEFAULT_DATABASE_PATH, get_all_reviews
    from schemas.concept_schema import ConceptSimulation, LaunchSummary, PersonaSimulation


def _build_persona_simulations(persona_simulations_df):
    """Wrap simulator persona rows in PersonaSimulation responses."""
    persona_simulations = []

    for _, persona_row in persona_simulations_df.iterrows():
        persona_simulations.append(
            PersonaSimulation(
                cluster=int(persona_row["cluster"]),
                persona_name=persona_row["persona_name"],
                review_count_used=int(persona_row["review_count_used"]),
                evidence_review_count=int(persona_row["evidence_review_count"]),
                evidence_average_rating=persona_row["evidence_average_rating"],
                evidence_sentiment_score=persona_row["evidence_sentiment_score"],
                simulated_rating=persona_row["simulated_rating"],
                likely_concern=persona_row["likely_concern"],
                confidence=persona_row["confidence"],
                simulation_note=persona_row["simulation_note"],
                persona_response=persona_row["persona_response"],
            )
        )

    return persona_simulations


def _build_concept_simulation(result):
    """Wrap a raw concept simulator result in a ConceptSimulation response."""
    if "error" in result:
        return ConceptSimulation(error=result["error"])

    return ConceptSimulation(
        product_name=result["product_name"],
        category=result["category"],
        price=result["price"],
        features=result["features"],
        description=result["description"],
        concept_text=result["concept_text"],
        persona_simulations=_build_persona_simulations(result["persona_simulations"]),
        launch_score=result["launch_score"],
        launch_label=result["launch_label"],
        recommendations=result["recommendations"],
        similar_review_count=result["similar_review_count"],
        simulation_note=result["simulation_note"],
    )


def _get_reviews_dataframe(reviews_df=None, db_path=DEFAULT_DATABASE_PATH):
    """Return provided reviews or load persisted reviews from the repository."""
    if reviews_df is not None:
        return reviews_df

    return get_all_reviews(db_path)


def simulate_concept(
    product_name,
    category,
    price,
    features,
    description,
    reviews_df=None,
    db_path=DEFAULT_DATABASE_PATH,
):
    """Run the existing product concept simulator for dashboard and service callers."""
    reviews_df = _get_reviews_dataframe(reviews_df, db_path)
    result = simulate_product_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
        reviews_df=reviews_df,
    )
    return _build_concept_simulation(result)


def build_launch_summary(simulation_result):
    """Build a compact launch summary from a concept simulation result."""
    if simulation_result.error:
        return LaunchSummary(error=simulation_result.error)

    return LaunchSummary(
        launch_score=simulation_result.launch_score,
        launch_label=simulation_result.launch_label,
        similar_review_count=simulation_result.similar_review_count,
        recommendations=simulation_result.recommendations,
        simulation_note=simulation_result.simulation_note,
    )


def build_persona_results(simulation_result):
    """Return persona simulation rows from a concept simulation result."""
    if simulation_result.error:
        return None

    return simulation_result.persona_simulations

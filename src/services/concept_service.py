"""Concept simulation service functions for MarketMind workflows."""

try:
    from src.concept_simulator import simulate_product_concept
except ImportError:
    from concept_simulator import simulate_product_concept


def simulate_concept(product_name, category, price, features, description):
    """Run the existing product concept simulator for dashboard and service callers."""
    return simulate_product_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )


def build_launch_summary(simulation_result):
    """Build a compact launch summary from a concept simulation result."""
    if "error" in simulation_result:
        return {"error": simulation_result["error"]}

    return {
        "launch_score": simulation_result["launch_score"],
        "launch_label": simulation_result["launch_label"],
        "similar_review_count": simulation_result["similar_review_count"],
        "recommendations": simulation_result["recommendations"],
        "simulation_note": simulation_result["simulation_note"],
    }


def build_persona_results(simulation_result):
    """Return persona simulation rows from a concept simulation result."""
    if "error" in simulation_result:
        return None

    return simulation_result["persona_simulations"]

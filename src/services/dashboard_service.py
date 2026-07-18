"""Dashboard preparation services for MarketMind."""

try:
    from src.review_repository import DEFAULT_DATABASE_PATH
    from src.schemas.dashboard_schema import (
        DashboardMetrics,
        DashboardResponse,
        DashboardTables,
    )
    from src.services import concept_service, product_service
except ImportError:
    from review_repository import DEFAULT_DATABASE_PATH
    from schemas.dashboard_schema import (
        DashboardMetrics,
        DashboardResponse,
        DashboardTables,
    )
    from services import concept_service, product_service


DEFAULT_DASHBOARD_DATA_PATH = DEFAULT_DATABASE_PATH


def load_dashboard_data(db_path=DEFAULT_DATABASE_PATH):
    """Load repository-backed review data for dashboard workflows."""
    return product_service.load_product_data(db_path)


def prepare_dashboard_metrics(result):
    """Prepare metric values from a product or concept result."""
    if result.error:
        return DashboardMetrics(error=result.error)

    if hasattr(result, "metrics"):
        metrics = result.metrics
        return DashboardMetrics(
            review_count=metrics["review_count"],
            average_rating=metrics["average_rating"],
            negative_percentage=metrics["negative_percentage"],
            health_score=result.health_score,
            health_label=result.health_label,
        )

    launch_summary = concept_service.build_launch_summary(result)
    return DashboardMetrics(
        launch_score=launch_summary.launch_score,
        launch_label=launch_summary.launch_label,
        similar_review_count=launch_summary.similar_review_count,
        recommendations=launch_summary.recommendations,
        simulation_note=launch_summary.simulation_note,
        error=launch_summary.error,
    )


def prepare_dashboard_tables(result):
    """Prepare dashboard table data from product analysis results."""
    if result.error:
        return DashboardTables()

    if hasattr(result, "sentiment_distribution"):
        return DashboardTables(
            sentiment_distribution=result.sentiment_distribution,
            category_summary=result.category_summary,
            matched_product_names=result.matched_product_names,
        )

    return DashboardTables(persona_simulations=result.persona_simulations)


def analyze_product_for_dashboard(product_query, reviews_df=None):
    """Analyze one product for dashboard display."""
    result = product_service.analyze_product(product_query, reviews_df=reviews_df)
    return DashboardResponse(
        result=result,
        metrics=prepare_dashboard_metrics(result),
        tables=prepare_dashboard_tables(result),
        error=result.error,
    )


def simulate_concept_for_dashboard(
    product_name,
    category,
    price,
    features,
    description,
):
    """Simulate a product concept for dashboard display."""
    result = concept_service.simulate_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    return DashboardResponse(
        result=result,
        metrics=prepare_dashboard_metrics(result),
        tables=prepare_dashboard_tables(result),
        error=result.error,
    )

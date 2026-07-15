"""Build AI-ready context from existing MarketMind services."""

try:
    from src.schemas.ai_schema import AIContext
    from src.services import concept_service, product_service
except ImportError:
    from schemas.ai_schema import AIContext
    from services import concept_service, product_service


def _extract_strengths(product_health):
    """Extract simple strengths from existing product health outputs."""
    strengths = []
    if product_health is None or product_health.error:
        return strengths

    metrics = product_health.metrics
    if metrics.get("average_rating", 0) >= 4:
        strengths.append("High average rating")
    if metrics.get("positive_percentage", 0) >= 50:
        strengths.append("Positive sentiment majority")
    if metrics.get("negative_percentage", 100) <= 25:
        strengths.append("Low negative feedback share")
    if product_health.health_label:
        strengths.append(product_health.health_label)

    return strengths


def build_product_context(product_query, comparison_queries=None):
    """Build AI context for an existing product analysis."""
    product_health = product_service.get_product_health(product_query)
    if product_health.error:
        return AIContext(
            product_query=product_query,
            product_health=product_health,
            error=product_health.error,
        )

    comparison = None
    if comparison_queries:
        comparison = product_service.compare_products(comparison_queries)

    return AIContext(
        product_query=product_query,
        product_health=product_health,
        sentiment_distribution=product_health.sentiment_distribution,
        complaint_summary=product_health.category_summary,
        strengths=_extract_strengths(product_health),
        recommendations=product_health.recommendations,
        comparison=comparison,
    )


def build_launch_context(product_name, category, price, features, description):
    """Build AI context for a product concept launch simulation."""
    concept = concept_service.simulate_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    if concept.error:
        return AIContext(concept=concept, error=concept.error)

    return AIContext(
        product_query=product_name,
        personas=concept.persona_simulations,
        launch_score=concept.launch_score,
        launch_label=concept.launch_label,
        recommendations=concept.recommendations,
        concept=concept,
    )


def build_business_context(
    product_query=None,
    comparison_queries=None,
    product_name=None,
    category="",
    price="",
    features="",
    description=None,
):
    """Build combined AI context for a deterministic business report."""
    product_context = None
    launch_context = None

    if product_query:
        product_context = build_product_context(product_query, comparison_queries)
        if product_context.error:
            return product_context

    if product_name and description:
        launch_context = build_launch_context(
            product_name=product_name,
            category=category,
            price=price,
            features=features,
            description=description,
        )
        if launch_context.error:
            return launch_context

    return AIContext(
        product_query=product_query or product_name,
        product_health=product_context.product_health if product_context else None,
        sentiment_distribution=(
            product_context.sentiment_distribution if product_context else {}
        ),
        complaint_summary=product_context.complaint_summary if product_context else None,
        strengths=product_context.strengths if product_context else [],
        personas=launch_context.personas if launch_context else [],
        launch_score=launch_context.launch_score if launch_context else None,
        launch_label=launch_context.launch_label if launch_context else None,
        recommendations=(
            product_context.recommendations if product_context else []
        )
        + (launch_context.recommendations if launch_context else []),
        comparison=product_context.comparison if product_context else None,
        concept=launch_context.concept if launch_context else None,
    )

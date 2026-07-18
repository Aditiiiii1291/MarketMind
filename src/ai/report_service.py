"""Report builders for AI-ready MarketMind context."""

from datetime import datetime, timezone

try:
    from src.ai import context_builder, prompt_templates
    from src.schemas.ai_schema import (
        BusinessReport,
        LaunchAnalysis,
        PersonaSummary,
        ProductInsight,
    )
except ImportError:
    from ai import context_builder, prompt_templates
    from schemas.ai_schema import (
        BusinessReport,
        LaunchAnalysis,
        PersonaSummary,
        ProductInsight,
    )


def build_product_summary(context):
    """Build a deterministic product summary from AI context."""
    if context.error:
        return ProductInsight(
            product_query=context.product_query,
            health_score=None,
            health_label=None,
            review_count=None,
            average_rating=None,
            prompt=prompt_templates.build_product_summary_prompt(context),
            error=context.error,
        )

    metrics = context.product_health.metrics
    return ProductInsight(
        product_query=context.product_query,
        health_score=context.product_health.health_score,
        health_label=context.product_health.health_label,
        review_count=metrics["review_count"],
        average_rating=metrics["average_rating"],
        strengths=context.strengths,
        recommendations=context.product_health.recommendations,
        prompt=prompt_templates.build_product_summary_prompt(context),
    )


def build_launch_analysis(context):
    """Build a deterministic launch analysis from AI context."""
    if context.error:
        return LaunchAnalysis(
            product_name=context.product_query,
            launch_score=None,
            launch_label=None,
            similar_review_count=None,
            prompt=prompt_templates.build_launch_prompt(context),
            error=context.error,
        )

    similar_review_count = None
    if context.concept is not None:
        similar_review_count = context.concept.similar_review_count

    return LaunchAnalysis(
        product_name=context.product_query,
        launch_score=context.launch_score,
        launch_label=context.launch_label,
        similar_review_count=similar_review_count,
        recommendations=context.recommendations,
        prompt=prompt_templates.build_launch_prompt(context),
    )


def build_persona_summary(context):
    """Build a deterministic persona summary from AI context."""
    return PersonaSummary(
        personas=context.personas,
        prompt=prompt_templates.build_persona_prompt(context),
        error=context.error,
    )


def build_comparison_summary(context):
    """Build a deterministic comparison summary from AI context."""
    if context.error:
        return context.error
    if context.comparison is None:
        return "No comparison data was requested."

    return context.comparison.insight


def build_business_report(context):
    """Build a deterministic business report from AI context."""
    product_insight = None
    launch_analysis = None

    if context.product_health is not None:
        product_insight = build_product_summary(context)
    if context.concept is not None:
        launch_analysis = build_launch_analysis(context)

    return BusinessReport(
        product_insight=product_insight,
        launch_analysis=launch_analysis,
        persona_summary=build_persona_summary(context),
        comparison_summary=build_comparison_summary(context),
        prompt=prompt_templates.build_business_report_prompt(context),
        error=context.error,
    )


def build_product_summary_for_query(product_query, comparison_queries=None):
    """Build a product insight report for one product query."""
    context = context_builder.build_product_context(product_query, comparison_queries)
    return build_product_summary(context)


def build_launch_analysis_for_concept(product_name, category, price, features, description):
    """Build a launch analysis report for one product concept."""
    context = context_builder.build_launch_context(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    return build_launch_analysis(context)


def build_persona_summary_for_concept(product_name, category, price, features, description):
    """Build a persona summary report for one product concept."""
    context = context_builder.build_launch_context(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    return build_persona_summary(context)


def build_business_report_for_inputs(
    product_query=None,
    comparison_queries=None,
    product_name=None,
    category="",
    price="",
    features="",
    description=None,
):
    """Build a deterministic business report from product and concept inputs."""
    context = context_builder.build_business_context(
        product_query=product_query,
        comparison_queries=comparison_queries,
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    return build_business_report(context)


def build_product_summary_ai_for_query(product_query, comparison_queries=None):
    """Build an optional Gemini product analysis with deterministic fallback."""
    context = context_builder.build_product_context(product_query, comparison_queries)
    deterministic = build_product_summary(context)
    return _build_optional_gemini_response(
        context=context,
        deterministic=deterministic,
        generate_method="generate_product_analysis",
    )


def build_launch_analysis_ai_for_concept(
    product_name,
    category,
    price,
    features,
    description,
):
    """Build an optional Gemini launch analysis with deterministic fallback."""
    context = context_builder.build_launch_context(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    deterministic = build_launch_analysis(context)
    return _build_optional_gemini_response(
        context=context,
        deterministic=deterministic,
        generate_method="generate_launch_analysis",
    )


def build_persona_summary_ai_for_concept(
    product_name,
    category,
    price,
    features,
    description,
):
    """Build an optional Gemini persona report with deterministic fallback."""
    context = context_builder.build_launch_context(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    deterministic = build_persona_summary(context)
    return _build_optional_gemini_response(
        context=context,
        deterministic=deterministic,
        generate_method="generate_persona_report",
    )


def build_business_report_ai_for_inputs(
    product_query=None,
    comparison_queries=None,
    product_name=None,
    category="",
    price="",
    features="",
    description=None,
):
    """Build an optional Gemini business report with deterministic fallback."""
    context = context_builder.build_business_context(
        product_query=product_query,
        comparison_queries=comparison_queries,
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    deterministic = build_business_report(context)
    return _build_optional_gemini_response(
        context=context,
        deterministic=deterministic,
        generate_method="generate_business_report",
    )


def _build_optional_gemini_response(context, deterministic, generate_method):
    generated_at = _utc_now()
    client = _get_gemini_client()

    if context.error:
        return _build_deterministic_response(
            deterministic=deterministic,
            generated_at=generated_at,
            fallback_reason="analysis_error",
        )

    if not client.is_available():
        return _build_deterministic_response(
            deterministic=deterministic,
            generated_at=generated_at,
            fallback_reason=client.unavailable_reason(),
        )

    result = getattr(client, generate_method)(context)
    if result["ok"]:
        return {
            "source": "gemini",
            "model": result["model"],
            "generated_at": generated_at,
            "analysis": result["analysis"],
        }

    return _build_deterministic_response(
        deterministic=deterministic,
        generated_at=generated_at,
        fallback_reason=result.get("error", "gemini_unavailable"),
    )


def _build_deterministic_response(deterministic, generated_at, fallback_reason):
    return {
        "source": "deterministic",
        "model": None,
        "generated_at": generated_at,
        "fallback_reason": fallback_reason or "gemini_unavailable",
        "analysis": deterministic,
    }


def _get_gemini_client():
    try:
        from src.ai import gemini_client
    except ImportError:
        from ai import gemini_client

    return gemini_client.gemini_client


def _utc_now():
    return datetime.now(timezone.utc).isoformat()

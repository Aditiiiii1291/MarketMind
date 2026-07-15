"""Prompt template builders for future MarketMind LLM integration."""


def build_product_summary_prompt(context):
    """Build a prompt for a future product summary LLM call."""
    return (
        "Summarize the product health signals using only the provided "
        f"MarketMind context for product query: {context.product_query}."
    )


def build_launch_prompt(context):
    """Build a prompt for a future launch-readiness LLM call."""
    return (
        "Analyze launch readiness using only the provided MarketMind concept "
        f"simulation context for: {context.product_query}."
    )


def build_persona_prompt(context):
    """Build a prompt for a future persona-analysis LLM call."""
    return (
        "Summarize persona reactions using only the provided simulated persona "
        f"context for: {context.product_query}."
    )


def build_comparison_prompt(context):
    """Build a prompt for a future product-comparison LLM call."""
    return (
        "Compare products using only the provided MarketMind comparison data "
        f"for: {context.product_query}."
    )


def build_business_report_prompt(context):
    """Build a prompt for a future business-report LLM call."""
    return (
        "Create a business report using only the provided MarketMind product, "
        f"launch, persona, and comparison context for: {context.product_query}."
    )

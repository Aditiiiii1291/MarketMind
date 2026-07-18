"""Prompt template builders for MarketMind AI report generation."""

import json


GEMINI_SYSTEM_PROMPT = """You are a Senior Product Manager and Customer Insights Analyst.

You analyse structured customer feedback and business analytics.

Never invent statistics.

Only use the supplied context.

Provide concise, professional recommendations."""

GEMINI_REPORT_SECTIONS = (
    "Executive Summary",
    "Top Strengths",
    "Major Weaknesses",
    "Customer Pain Points",
    "Business Risks",
    "Launch Recommendation",
    "Customer Persona Insights",
    "Actionable Product Improvements",
    "Priority Recommendations",
)


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


def build_gemini_product_analysis_prompt(context_payload):
    """Build a Gemini prompt for product analysis."""
    return _build_gemini_prompt("product analysis", context_payload)


def build_gemini_business_report_prompt(context_payload):
    """Build a Gemini prompt for a business report."""
    return _build_gemini_prompt("business report", context_payload)


def build_gemini_launch_analysis_prompt(context_payload):
    """Build a Gemini prompt for launch analysis."""
    return _build_gemini_prompt("launch analysis", context_payload)


def build_gemini_persona_report_prompt(context_payload):
    """Build a Gemini prompt for persona analysis."""
    return _build_gemini_prompt("customer persona report", context_payload)


def _build_gemini_prompt(report_type, context_payload):
    sections = "\n".join(f"- {section}" for section in GEMINI_REPORT_SECTIONS)
    context_json = json.dumps(context_payload, indent=2, default=str)
    return (
        f"Create a concise professional Markdown {report_type}.\n\n"
        "Use only the supplied structured MarketMind AIContext below. "
        "Do not infer or invent statistics, review counts, ratings, or customer claims. "
        "If a section has limited evidence, say so plainly.\n\n"
        "Include these Markdown sections:\n"
        f"{sections}\n\n"
        "MarketMind AIContext:\n"
        f"```json\n{context_json}\n```"
    )

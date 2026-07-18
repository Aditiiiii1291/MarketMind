"""Optional Google Gemini client for MarketMind AI reports."""

import time
from dataclasses import asdict, is_dataclass

import pandas as pd

try:
    from src.config import GOOGLE_API_KEY, GOOGLE_MODEL
    from src.logger import logger
    from src.ai import prompt_templates
except ImportError:
    from config import GOOGLE_API_KEY, GOOGLE_MODEL
    from logger import logger
    from ai import prompt_templates

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GeminiClient:
    """Reusable Gemini client with safe fallback-friendly error handling."""

    def __init__(self, api_key=GOOGLE_API_KEY, model=GOOGLE_MODEL):
        self.api_key = api_key
        self.model = model or "gemini-2.5-flash"
        self._client = None
        self._disabled_reason = None

        if not self.api_key:
            self._disabled_reason = "missing_api_key"
            return
        if genai is None:
            self._disabled_reason = "google_genai_not_installed"
            return

        try:
            self._client = genai.Client(api_key=self.api_key)
        except Exception as error:
            self._disabled_reason = error.__class__.__name__
            logger.warning(
                "Gemini client initialization failed: status=unavailable reason=%s",
                self._disabled_reason,
            )

    def is_available(self):
        """Return whether Gemini can be called for this process."""
        return self._client is not None

    def unavailable_reason(self):
        """Return a non-sensitive reason Gemini is unavailable."""
        return self._disabled_reason

    def generate_product_analysis(self, context):
        """Generate a product analysis Markdown report from safe AIContext."""
        return self._generate(
            prompt_templates.build_gemini_product_analysis_prompt(
                _safe_context_payload(context)
            )
        )

    def generate_business_report(self, context):
        """Generate a business Markdown report from safe AIContext."""
        return self._generate(
            prompt_templates.build_gemini_business_report_prompt(
                _safe_context_payload(context)
            )
        )

    def generate_launch_analysis(self, context):
        """Generate a launch-readiness Markdown report from safe AIContext."""
        return self._generate(
            prompt_templates.build_gemini_launch_analysis_prompt(
                _safe_context_payload(context)
            )
        )

    def generate_persona_report(self, context):
        """Generate a persona Markdown report from safe AIContext."""
        return self._generate(
            prompt_templates.build_gemini_persona_report_prompt(
                _safe_context_payload(context)
            )
        )

    def _generate(self, prompt):
        if not self.is_available():
            return {
                "ok": False,
                "model": self.model,
                "error": self._disabled_reason or "unavailable",
            }

        start_time = time.perf_counter()
        status = "error"
        token_usage = None

        try:
            config = None
            if types is not None:
                config = types.GenerateContentConfig(
                    system_instruction=prompt_templates.GEMINI_SYSTEM_PROMPT,
                    temperature=0.2,
                )

            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            text = (getattr(response, "text", "") or "").strip()
            if not text:
                raise RuntimeError("Gemini returned an empty response.")

            usage = getattr(response, "usage_metadata", None)
            token_usage = _extract_token_usage(usage)
            status = "success"
            return {
                "ok": True,
                "model": self.model,
                "analysis": text,
                "token_usage": token_usage,
            }
        except Exception as error:
            status = error.__class__.__name__
            return {
                "ok": False,
                "model": self.model,
                "error": status,
            }
        finally:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Gemini request completed: model=%s status=%s latency_ms=%s token_usage=%s",
                self.model,
                status,
                latency_ms,
                token_usage,
            )


def _safe_context_payload(context):
    """Serialize AIContext without raw review rows, CSV data, or DB records."""
    product_health = context.product_health
    concept = context.concept
    comparison = context.comparison

    payload = {
        "product_query": context.product_query,
        "product_health": None,
        "sentiment_distribution": _safe_value(context.sentiment_distribution),
        "complaint_summary": _safe_value(context.complaint_summary),
        "strengths": _safe_value(context.strengths),
        "personas": _safe_value(context.personas),
        "launch_score": context.launch_score,
        "launch_label": context.launch_label,
        "recommendations": _safe_value(context.recommendations),
        "comparison_summary": getattr(comparison, "insight", None),
        "concept": None,
        "error": context.error,
    }

    if product_health is not None:
        payload["product_health"] = {
            "product_query": product_health.product_query,
            "matched_product_names": _safe_value(product_health.matched_product_names),
            "metrics": _safe_value(product_health.metrics),
            "sentiment_distribution": _safe_value(
                product_health.sentiment_distribution
            ),
            "health_score": product_health.health_score,
            "health_label": product_health.health_label,
            "category_summary": _safe_value(product_health.category_summary),
            "recommendations": _safe_value(product_health.recommendations),
            "error": product_health.error,
        }

    if concept is not None:
        payload["concept"] = {
            "product_name": concept.product_name,
            "category": concept.category,
            "price": concept.price,
            "features": concept.features,
            "description": concept.description,
            "persona_simulations": _safe_value(concept.persona_simulations),
            "launch_score": concept.launch_score,
            "launch_label": concept.launch_label,
            "recommendations": _safe_value(concept.recommendations),
            "similar_review_count": concept.similar_review_count,
            "simulation_note": concept.simulation_note,
            "error": concept.error,
        }

    return payload


def _safe_value(value):
    if value is None:
        return None
    if is_dataclass(value):
        return _safe_value(asdict(value))
    if isinstance(value, pd.DataFrame):
        return value.where(pd.notna(value), None).to_dict(orient="records")
    if isinstance(value, dict):
        return {key: _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _extract_token_usage(usage):
    if usage is None:
        return None

    fields = (
        "prompt_token_count",
        "candidates_token_count",
        "total_token_count",
    )
    usage_payload = {}
    for field in fields:
        value = getattr(usage, field, None)
        if value is not None:
            usage_payload[field] = value

    return usage_payload or None


gemini_client = GeminiClient()

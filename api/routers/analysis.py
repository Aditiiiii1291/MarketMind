"""AI-readiness analysis API routes for MarketMind."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth.security import get_current_user
from api.routers import to_jsonable
from src.ai import report_service


router = APIRouter(prefix="/analysis", tags=["analysis"])


def _raise_for_analysis_error(error):
    """Convert deterministic analysis errors into HTTP responses."""
    if not error:
        return
    if "No reviews found" in error:
        raise HTTPException(status_code=404, detail=error)
    raise HTTPException(status_code=400, detail=error)


def _raise_for_ai_analysis_error(result):
    """Convert fallback deterministic analysis errors into HTTP responses."""
    analysis = result.get("analysis")
    error = getattr(analysis, "error", None)
    _raise_for_analysis_error(error)


@router.get(
    "/product",
    summary="Build product analysis",
    description="Return deterministic AI-ready product analysis for one product query.",
    response_description="Structured ProductInsight response.",
)
def get_product_analysis(
    query: str = Query(..., min_length=1),
    current_user=Depends(get_current_user),
):
    """Return deterministic product analysis for one product query."""
    result = report_service.build_product_summary_for_query(query)
    _raise_for_analysis_error(result.error)
    return to_jsonable(result)


@router.get(
    "/product-ai",
    summary="Build Gemini product analysis",
    description="Return optional Gemini product analysis with deterministic fallback.",
    response_description="Markdown report when Gemini is available, otherwise deterministic ProductInsight.",
)
def get_product_ai_analysis(
    query: str = Query(..., min_length=1),
    current_user=Depends(get_current_user),
):
    """Return optional Gemini product analysis for one product query."""
    result = report_service.build_product_summary_ai_for_query(query)
    _raise_for_ai_analysis_error(result)
    return to_jsonable(result)


@router.get(
    "/launch",
    summary="Build launch analysis",
    description="Return deterministic AI-ready launch analysis for a concept.",
    response_description="Structured LaunchAnalysis response.",
)
def get_launch_analysis(
    product_name: str = Query(..., min_length=1),
    description: str = Query(..., min_length=1),
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return deterministic launch analysis for one product concept."""
    result = report_service.build_launch_analysis_for_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_analysis_error(result.error)
    return to_jsonable(result)


@router.get(
    "/launch-ai",
    summary="Build Gemini launch analysis",
    description="Return optional Gemini launch analysis with deterministic fallback.",
    response_description="Markdown report when Gemini is available, otherwise deterministic LaunchAnalysis.",
)
def get_launch_ai_analysis(
    product_name: str = Query(..., min_length=1),
    description: str = Query(..., min_length=1),
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return optional Gemini launch analysis for one product concept."""
    result = report_service.build_launch_analysis_ai_for_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_ai_analysis_error(result)
    return to_jsonable(result)


@router.get(
    "/personas",
    summary="Build persona analysis",
    description="Return deterministic AI-ready persona analysis for a concept.",
    response_description="Structured PersonaSummary response.",
)
def get_persona_analysis(
    product_name: str = Query(..., min_length=1),
    description: str = Query(..., min_length=1),
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return deterministic persona analysis for one product concept."""
    result = report_service.build_persona_summary_for_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_analysis_error(result.error)
    return to_jsonable(result)


@router.get(
    "/personas-ai",
    summary="Build Gemini persona analysis",
    description="Return optional Gemini persona analysis with deterministic fallback.",
    response_description="Markdown report when Gemini is available, otherwise deterministic PersonaSummary.",
)
def get_persona_ai_analysis(
    product_name: str = Query(..., min_length=1),
    description: str = Query(..., min_length=1),
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return optional Gemini persona analysis for one product concept."""
    result = report_service.build_persona_summary_ai_for_concept(
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_ai_analysis_error(result)
    return to_jsonable(result)


@router.get(
    "/report",
    summary="Build business report",
    description="Return a deterministic AI-ready business report from services.",
    response_description="Structured BusinessReport response.",
)
def get_business_report(
    product_query: Optional[str] = None,
    comparison_products: Optional[List[str]] = Query(None),
    product_name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return a deterministic business report for product and concept inputs."""
    result = report_service.build_business_report_for_inputs(
        product_query=product_query,
        comparison_queries=comparison_products,
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_analysis_error(result.error)
    return to_jsonable(result)


@router.get(
    "/report-ai",
    summary="Build Gemini business report",
    description="Return optional Gemini business report with deterministic fallback.",
    response_description="Markdown report when Gemini is available, otherwise deterministic BusinessReport.",
)
def get_business_ai_report(
    product_query: Optional[str] = None,
    comparison_products: Optional[List[str]] = Query(None),
    product_name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "",
    price: str = "",
    features: str = "",
    current_user=Depends(get_current_user),
):
    """Return optional Gemini business report for product and concept inputs."""
    result = report_service.build_business_report_ai_for_inputs(
        product_query=product_query,
        comparison_queries=comparison_products,
        product_name=product_name,
        category=category,
        price=price,
        features=features,
        description=description,
    )
    _raise_for_ai_analysis_error(result)
    return to_jsonable(result)

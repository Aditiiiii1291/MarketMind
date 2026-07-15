"""Product API routes backed by MarketMind product services."""

from typing import List

from fastapi import APIRouter, HTTPException, Query

from api.routers import to_jsonable
from src.services import product_service


router = APIRouter(prefix="/products", tags=["products"])


def _raise_for_product_error(error):
    """Convert product service errors into HTTP exceptions."""
    if not error:
        return
    if "non-empty" in error:
        raise HTTPException(status_code=400, detail=error)
    if "No reviews found" in error:
        raise HTTPException(status_code=404, detail=error)
    raise HTTPException(status_code=500, detail=error)


@router.get(
    "/search",
    summary="Search products",
    description="Search processed review data for product names matching a query.",
    response_description="Matching product names and review count.",
)
def search_products(query: str = Query(..., min_length=1), limit: int = Query(20, ge=1)):
    """Return product names and review count for a product search query."""
    try:
        reviews_df = product_service.get_product_reviews(query)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if reviews_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f'No reviews found for product: "{query.strip()}"',
        )

    product_names = reviews_df["product_name"].dropna().unique().tolist()
    return {
        "query": query,
        "matched_product_names": product_names[:limit],
        "review_count": len(reviews_df),
    }


@router.get(
    "/health",
    summary="Analyze product health",
    description="Return product health analysis for one product query.",
    response_description="Structured product health DTO.",
)
def get_product_health(query: str = Query(..., min_length=1)):
    """Return the ProductHealth service response for one product query."""
    try:
        result = product_service.get_product_health(query)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    _raise_for_product_error(result.error)
    return to_jsonable(result)


@router.get(
    "/summary",
    summary="Get product summary",
    description="Return a compact product summary for one product query.",
    response_description="Structured product summary DTO.",
)
def get_product_summary(query: str = Query(..., min_length=1)):
    """Return the ProductSummary service response for one product query."""
    try:
        health = product_service.get_product_health(query)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    _raise_for_product_error(health.error)
    return to_jsonable(product_service.get_product_summary(health))


@router.get(
    "/compare",
    summary="Compare products",
    description="Compare two to five product queries using product health scores.",
    response_description="Structured product comparison DTO.",
)
def compare_products(products: List[str] = Query(...)):
    """Return product comparison results for two to five product queries."""
    clean_products = [product.strip() for product in products if product.strip()]
    if len(clean_products) < 2 or len(clean_products) > 5:
        raise HTTPException(
            status_code=400,
            detail="Please provide 2 to 5 product queries.",
        )

    try:
        result = product_service.compare_products(clean_products)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result.ranked_products.empty:
        raise HTTPException(status_code=404, detail="No matching products found.")

    return to_jsonable(result)

"""Dashboard API routes backed by MarketMind dashboard services."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth.security import get_current_user
from api.routers import to_jsonable
from src.services import dashboard_service


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "",
    summary="Get dashboard response",
    description="Return the existing dashboard service DTO for a product query.",
    response_description="Structured dashboard response DTO.",
)
def get_dashboard(
    query: str = Query("AWC-38", min_length=1),
    current_user=Depends(get_current_user),
):
    """Return a DashboardResponse service object for the dashboard product query."""
    try:
        result = dashboard_service.analyze_product_for_dashboard(query)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if result.error:
        if "No reviews found" in result.error:
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)

    return to_jsonable(result)

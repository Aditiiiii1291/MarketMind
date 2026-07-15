"""Concept API routes backed by MarketMind concept services."""

from typing import Dict

from fastapi import APIRouter, HTTPException

from api.routers import to_jsonable
from src.services import concept_service


router = APIRouter(prefix="/concept", tags=["concepts"])


@router.post(
    "/simulate",
    summary="Simulate concept feedback",
    description="Run the existing product concept simulator for a concept payload.",
    response_description="Structured concept simulation DTO.",
)
def simulate_concept(payload: Dict[str, str]):
    """Return a ConceptSimulation service response for a concept payload."""
    try:
        result = concept_service.simulate_concept(
            product_name=payload.get("product_name", ""),
            category=payload.get("category", ""),
            price=payload.get("price", ""),
            features=payload.get("features", ""),
            description=payload.get("description", ""),
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    return to_jsonable(result)


@router.get(
    "/example",
    summary="Get concept example",
    description="Return an example concept payload for the simulation endpoint.",
    response_description="Example concept simulation request payload.",
)
def get_concept_example():
    """Return an example concept simulation request payload."""
    return {
        "product_name": "Smart Water Bottle",
        "category": "Electronics",
        "price": "999",
        "features": "hydration reminders, temperature display, USB charging",
        "description": (
            "A smart water bottle with hydration reminders and a temperature "
            "display for daily use."
        ),
    }

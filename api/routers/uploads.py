"""Dataset upload API routes backed by MarketMind upload services."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.auth.security import get_current_user
from api.routers import to_jsonable
from src.services import upload_service


router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Upload review dataset",
    description="Upload a CSV review dataset and ingest it through the shared pipeline.",
    response_description="Structured upload ingestion result.",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV review dataset to upload."),
    current_user=Depends(get_current_user),
):
    """Upload and ingest one CSV dataset for the authenticated user."""
    try:
        content = await file.read()
        result = upload_service.save_uploaded_dataset(
            filename=file.filename,
            content=content,
            user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return to_jsonable(result)


@router.get(
    "/history",
    summary="Get upload history",
    description="Return upload history for the authenticated user.",
    response_description="Structured upload history response.",
)
def get_upload_history(current_user=Depends(get_current_user)):
    """Return upload history for the authenticated user."""
    return to_jsonable(upload_service.get_upload_history(current_user.id))


@router.get(
    "/{upload_id}",
    summary="Get upload detail",
    description="Return one upload metadata record for the authenticated user.",
    response_description="Structured upload history item.",
)
def get_upload_detail(upload_id: int, current_user=Depends(get_current_user)):
    """Return one upload detail record for the authenticated user."""
    upload = upload_service.get_upload_detail(upload_id, current_user.id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found.")

    return to_jsonable(upload)

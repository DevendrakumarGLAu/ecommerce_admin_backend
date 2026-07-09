"""Generic image upload endpoint backed by Supabase Storage (admin only)."""

from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.dependencies.auth import require_admin
from app.schemas.common import SuccessResponse
from app.schemas.upload import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/image",
    response_model=SuccessResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image to Supabase Storage (admin only)",
    description=(
        "Validates the file's content type and size, uploads it to Supabase Storage under a unique "
        "generated filename, and returns its public URL. Use the returned URL when creating/updating "
        "categories, products, product images, or settings."
    ),
    dependencies=[Depends(require_admin)],
)
async def upload_image(
    file: UploadFile = File(..., description="Image file (jpeg, png, webp, or gif)"),
    folder: Literal["products", "categories", "settings", "profile"] = Query(
        default="products", description="Storage sub-folder to organize uploads"
    ),
) -> SuccessResponse[UploadResponse]:
    url = await UploadService().upload_image(file, folder=folder)
    return SuccessResponse(message="Image uploaded successfully", data=UploadResponse(url=url))


@router.post(
    "/video",
    response_model=SuccessResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video to Supabase Storage (admin only)",
    description=(
        "Validates the file's content type and size, uploads it to Supabase Storage under a unique "
        "generated filename, and returns its public URL. Use the returned URL when attaching a video "
        "to a product."
    ),
    dependencies=[Depends(require_admin)],
)
async def upload_video(
    file: UploadFile = File(..., description="Video file (mp4, webm, or mov)"),
    folder: Literal["products"] = Query(default="products", description="Storage sub-folder to organize uploads"),
) -> SuccessResponse[UploadResponse]:
    url = await UploadService().upload_video(file, folder=folder)
    return SuccessResponse(message="Video uploaded successfully", data=UploadResponse(url=url))

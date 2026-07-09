"""Site settings endpoints — public read, admin-only update."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.schemas.common import SuccessResponse
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "",
    response_model=SuccessResponse[SettingsResponse],
    summary="Get site settings",
    description="Returns the site-wide settings (branding, contact info, social links, analytics ids).",
)
async def get_settings(db: AsyncSession = Depends(get_db)) -> SuccessResponse[SettingsResponse]:
    result = await SettingsService(db).get_settings()
    return SuccessResponse(data=result)


@router.put(
    "",
    response_model=SuccessResponse[SettingsResponse],
    summary="Update site settings (admin only)",
    description="Partially updates the site-wide settings.",
    dependencies=[Depends(require_admin)],
)
async def update_settings(
    payload: SettingsUpdate, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[SettingsResponse]:
    result = await SettingsService(db).update_settings(payload)
    return SuccessResponse(message="Settings updated", data=result)

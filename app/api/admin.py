"""Admin-only aggregate endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get(
    "/dashboard",
    response_model=SuccessResponse[DashboardStatsResponse],
    summary="Get admin dashboard statistics",
    description="Returns total product/category/user counts plus featured and recently added products.",
)
async def get_dashboard(db: AsyncSession = Depends(get_db)) -> SuccessResponse[DashboardStatsResponse]:
    stats = await DashboardService(db).get_stats()
    return SuccessResponse(data=stats)

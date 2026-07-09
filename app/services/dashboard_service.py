"""Business logic for the admin dashboard summary."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.product import ProductSummaryResponse

_FEATURED_LIMIT = 10
_RECENT_LIMIT = 10


class DashboardService:
    """Aggregates catalog and user statistics for the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)
        self.users = UserRepository(db)

    async def get_stats(self) -> DashboardStatsResponse:
        total_products = await self.products.count_active()
        total_categories = await self.categories.count(Category.deleted_at.is_(None))
        total_users = await self.users.count_all()
        featured = await self.products.list_featured(_FEATURED_LIMIT)
        recent = await self.products.list_recent(_RECENT_LIMIT)

        return DashboardStatsResponse(
            total_products=total_products,
            total_categories=total_categories,
            total_users=total_users,
            featured_products=[ProductSummaryResponse.model_validate(p) for p in featured],
            recent_products=[ProductSummaryResponse.model_validate(p) for p in recent],
        )

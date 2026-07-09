"""Admin dashboard schema."""

from pydantic import BaseModel

from app.schemas.product import ProductSummaryResponse


class DashboardStatsResponse(BaseModel):
    total_products: int
    total_categories: int
    total_users: int
    featured_products: list[ProductSummaryResponse]
    recent_products: list[ProductSummaryResponse]

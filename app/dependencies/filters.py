"""Query-parameter dependency for product search & filtering."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from fastapi import Query

from app.models.product import ProductStatus, StockStatus


@dataclass(slots=True)
class ProductFilterParams:
    """Optional filters accepted by the product listing endpoint."""

    search: str | None = None
    category_id: UUID | None = None
    category_slug: str | None = None
    brand: str | None = None
    featured: bool | None = None
    bestseller: bool | None = None
    new_arrival: bool | None = None
    stock_status: StockStatus | None = None
    status: ProductStatus | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None


def get_product_filter_params(
    search: str | None = Query(default=None, description="Search by title, brand, or category name"),
    category_id: UUID | None = Query(default=None, description="Filter by category id"),
    category_slug: str | None = Query(default=None, description="Filter by category slug"),
    brand: str | None = Query(default=None, description="Filter by exact brand name"),
    featured: bool | None = Query(default=None, description="Filter featured products"),
    bestseller: bool | None = Query(default=None, description="Filter bestseller products"),
    new_arrival: bool | None = Query(default=None, description="Filter new-arrival products"),
    stock_status: StockStatus | None = Query(default=None, description="Filter by stock status"),
    status: ProductStatus | None = Query(default=None, description="Filter by publication status"),
    price_min: Decimal | None = Query(default=None, ge=0, description="Minimum price"),
    price_max: Decimal | None = Query(default=None, ge=0, description="Maximum price"),
) -> ProductFilterParams:
    """FastAPI dependency yielding validated product filter parameters."""
    return ProductFilterParams(
        search=search,
        category_id=category_id,
        category_slug=category_slug,
        brand=brand,
        featured=featured,
        bestseller=bestseller,
        new_arrival=new_arrival,
        stock_status=stock_status,
        status=status,
        price_min=price_min,
        price_max=price_max,
    )

"""Business logic for products: CRUD, slug generation, filtering, and image management."""

from dataclasses import asdict
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.filters import ProductFilterParams
from app.dependencies.pagination import PaginationParams
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_marketplace_link import ProductMarketplaceLink
from app.models.product_video import ProductVideo
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_image_repository import ProductImageRepository
from app.repositories.product_marketplace_link_repository import ProductMarketplaceLinkRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_video_repository import ProductVideoRepository
from app.schemas.common import PaginatedData
from app.schemas.product import (
    MarketplaceLinkCreate,
    ProductCreate,
    ProductImageCreate,
    ProductSummaryResponse,
    ProductUpdate,
    ProductVideoCreate,
)
from app.services import cache_service
from app.services.upload_service import UploadService
from app.utils.exceptions import ConflictException, NotFoundException
from app.utils.slug import build_candidate_slug, generate_slug

_URL_FIELDS = ("canonical_url", "og_image")


class ProductService:
    """Orchestrates product CRUD, slug generation, filtering, caching, and image attachment."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)
        self.images = ProductImageRepository(db)
        self.videos = ProductVideoRepository(db)
        self.marketplace_links = ProductMarketplaceLinkRepository(db)
        self.upload_service = UploadService()

    async def _generate_unique_slug(self, title: str, exclude_id: uuid.UUID | None = None) -> str:
        base_slug = generate_slug(title)
        attempt = 0
        while True:
            candidate = build_candidate_slug(base_slug, attempt)
            if not await self.products.slug_exists(candidate, exclude_id=exclude_id):
                return candidate
            attempt += 1

    @staticmethod
    def _stringify_urls(data: dict[str, Any]) -> dict[str, Any]:
        for field in _URL_FIELDS:
            if data.get(field) is not None:
                data[field] = str(data[field])
        return data

    async def create(self, payload: ProductCreate) -> Product:
        """Create a product after validating category existence and SKU uniqueness."""
        category = await self.categories.get_by_id_active(payload.category_id)
        if category is None:
            raise NotFoundException("Category not found")

        if payload.sku and await self.products.sku_exists(payload.sku):
            raise ConflictException("A product with this SKU already exists")

        slug = await self._generate_unique_slug(payload.title)
        data = self._stringify_urls(payload.model_dump(exclude={"category_id"}))

        product = await self.products.create(category_id=payload.category_id, slug=slug, **data)
        await self.products.commit()
        await cache_service.invalidate_products_cache()
        return await self.products.get_by_id_active(product.id)

    async def update(self, product_id: uuid.UUID, payload: ProductUpdate) -> Product:
        """Partially update a product, regenerating the slug only if `title` changed."""
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "category_id" in update_data:
            category = await self.categories.get_by_id_active(update_data["category_id"])
            if category is None:
                raise NotFoundException("Category not found")

        if (
            update_data.get("sku")
            and update_data["sku"] != product.sku
            and await self.products.sku_exists(update_data["sku"], exclude_id=product_id)
        ):
            raise ConflictException("A product with this SKU already exists")

        if "title" in update_data and update_data["title"] != product.title:
            update_data["slug"] = await self._generate_unique_slug(update_data["title"], exclude_id=product_id)

        update_data = self._stringify_urls(update_data)

        await self.products.update(product, **update_data)
        await self.products.commit()
        await cache_service.invalidate_products_cache()
        return await self.products.get_by_id_active(product_id)

    async def delete(self, product_id: uuid.UUID) -> None:
        """Soft-delete a product."""
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        await self.products.update(product, deleted_at=datetime.now(timezone.utc))
        await self.products.commit()
        await cache_service.invalidate_products_cache()

    async def get_by_slug(self, slug: str) -> Product:
        product = await self.products.get_by_slug(slug)
        if product is None:
            raise NotFoundException("Product not found")
        return product

    async def get_by_id(self, product_id: uuid.UUID) -> Product:
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        return product

    async def list_products(
        self, pagination: PaginationParams, filters: ProductFilterParams
    ) -> PaginatedData[ProductSummaryResponse]:
        """List products with search/filter/sort support, cached per unique query."""
        schema = PaginatedData[ProductSummaryResponse]
        # filter_signature = "|".join(f"{k}={v}" for k, v in sorted(vars(filters).items()))
        filter_signature = "|".join(
f"{k}={v}" for k, v in sorted(asdict(filters).items()))
        cache_key = cache_service.build_products_list_key(
            f"{pagination.page}:{pagination.limit}:{pagination.sort}:{pagination.order}:{filter_signature}"
        )

        cached = await cache_service.get_cached(cache_key)
        if cached is not None:
            return schema.model_validate(cached)

        items, total = await self.products.list_paginated(pagination, filters)
        result = schema.build(
            items=[ProductSummaryResponse.model_validate(item) for item in items],
            page=pagination.page,
            limit=pagination.limit,
            total=total,
        )
        await cache_service.set_cached(cache_key, result.model_dump(mode="json"))
        return result

    async def add_image(self, product_id: uuid.UUID, payload: ProductImageCreate) -> ProductImage:
        """Attach an already-uploaded image (see UploadService) to a product."""
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        image = await self.images.create(
            product_id=product_id,
            image_url=str(payload.image_url),
            alt_text=payload.alt_text,
            display_order=payload.display_order,
        )
        await self.images.commit()
        await cache_service.invalidate_products_cache()
        return image

    async def remove_image(self, product_id: uuid.UUID, image_id: uuid.UUID) -> None:
        """Detach and permanently delete a product image, including its storage object."""
        image = await self.images.get_by_id(image_id)
        if image is None or image.product_id != product_id:
            raise NotFoundException("Product image not found")

        image_url = image.image_url
        await self.images.delete(image)
        await self.images.commit()
        await self.upload_service.delete_file(image_url)
        await cache_service.invalidate_products_cache()

    async def add_video(self, product_id: uuid.UUID, payload: ProductVideoCreate) -> ProductVideo:
        """Attach an already-uploaded video (see UploadService) to a product."""
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        video = await self.videos.create(
            product_id=product_id,
            video_url=str(payload.video_url),
            thumbnail_url=str(payload.thumbnail_url) if payload.thumbnail_url else None,
            caption=payload.caption,
            display_order=payload.display_order,
        )
        await self.videos.commit()
        await cache_service.invalidate_products_cache()
        return video

    async def remove_video(self, product_id: uuid.UUID, video_id: uuid.UUID) -> None:
        """Detach and permanently delete a product video, including its storage object."""
        video = await self.videos.get_by_id(video_id)
        if video is None or video.product_id != product_id:
            raise NotFoundException("Product video not found")

        video_url = video.video_url
        await self.videos.delete(video)
        await self.videos.commit()
        await self.upload_service.delete_file(video_url)
        await cache_service.invalidate_products_cache()

    async def add_marketplace_link(
        self, product_id: uuid.UUID, payload: MarketplaceLinkCreate
    ) -> ProductMarketplaceLink:
        """Attach a "buy it here" link (Amazon, Flipkart, Meesho, etc.) to a product."""
        product = await self.products.get_by_id_active(product_id)
        if product is None:
            raise NotFoundException("Product not found")

        link = await self.marketplace_links.create(
            product_id=product_id,
            platform=payload.platform,
            custom_label=payload.custom_label,
            url=str(payload.url),
            display_order=payload.display_order,
        )
        await self.marketplace_links.commit()
        await cache_service.invalidate_products_cache()
        return link

    async def remove_marketplace_link(self, product_id: uuid.UUID, link_id: uuid.UUID) -> None:
        """Detach a marketplace link from a product."""
        link = await self.marketplace_links.get_by_id(link_id)
        if link is None or link.product_id != product_id:
            raise NotFoundException("Marketplace link not found")

        await self.marketplace_links.delete(link)
        await self.marketplace_links.commit()
        await cache_service.invalidate_products_cache()

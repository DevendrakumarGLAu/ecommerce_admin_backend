"""Business logic for the single-row site settings table."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services import cache_service


class SettingsService:
    """Orchestrates read/update of the site-wide settings singleton, with caching."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings_repo = SettingsRepository(db)

    async def get_settings(self) -> SettingsResponse:
        cached = await cache_service.get_cached(cache_service.SETTINGS_KEY)
        if cached is not None:
            return SettingsResponse.model_validate(cached)

        settings_row = await self.settings_repo.get_singleton()
        if settings_row is None:
            settings_row = await self.settings_repo.create()
            await self.settings_repo.commit()

        response = SettingsResponse.model_validate(settings_row)
        await cache_service.set_cached(cache_service.SETTINGS_KEY, response.model_dump(mode="json"))
        return response

    async def update_settings(self, payload: SettingsUpdate) -> SettingsResponse:
        """Update (or lazily create) the settings row, then refresh the cache."""
        settings_row = await self.settings_repo.get_singleton()
        update_data = payload.model_dump(exclude_unset=True)

        if settings_row is None:
            settings_row = await self.settings_repo.create(**update_data)
        else:
            settings_row = await self.settings_repo.update(settings_row, **update_data)
        await self.settings_repo.commit()

        await cache_service.invalidate_settings_cache()
        response = SettingsResponse.model_validate(settings_row)
        await cache_service.set_cached(cache_service.SETTINGS_KEY, response.model_dump(mode="json"))
        return response

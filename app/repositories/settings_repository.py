"""Data access for the single-row `Settings` table."""

from sqlalchemy import select

from app.models.settings import Settings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    model = Settings

    async def get_singleton(self) -> Settings | None:
        stmt = select(Settings).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

"""Add hero_banner_url, hero_banner_title, hero_banner_subtitle to settings.

Revision ID: 0005_settings_hero_banner
Revises: 0004_product_videos
Create Date: 2026-07-09 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_settings_hero_banner"
down_revision: Union[str, None] = "0004_product_videos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("settings", sa.Column("hero_banner_url", sa.String(500), nullable=True))
    op.add_column("settings", sa.Column("hero_banner_title", sa.String(200), nullable=True))
    op.add_column("settings", sa.Column("hero_banner_subtitle", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("settings", "hero_banner_subtitle")
    op.drop_column("settings", "hero_banner_title")
    op.drop_column("settings", "hero_banner_url")

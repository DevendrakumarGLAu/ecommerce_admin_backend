"""Add 'super_admin' to the users.role check constraint.

Revision ID: 0007_super_admin_role
Revises: 0006_category_active_product_owner
Create Date: 2026-07-10 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0007_super_admin_role"
down_revision: Union[str, None] = "0006_category_active_owner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint("ck_users_role", "users", "role IN ('super_admin', 'admin', 'customer')")


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint("ck_users_role", "users", "role IN ('admin', 'customer')")

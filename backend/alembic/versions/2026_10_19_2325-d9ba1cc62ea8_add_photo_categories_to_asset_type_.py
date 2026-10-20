"""add_photo_categories_to_asset_type_config

Revision ID: d9ba1cc62ea8
Revises: alembic_initial
Create Date: 2026-10-19 23:25:54.570494+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9ba1cc62ea8'
down_revision: Union[str, None] = 'alembic_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("asset_type_configs")]
    if "photo_categories" not in columns:
        op.add_column('asset_type_configs', 
            sa.Column('photo_categories', sa.Text(), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("asset_type_configs")]
    if "photo_categories" in columns:
        op.drop_column('asset_type_configs', 'photo_categories')

"""add_archived_to_room_inventory_prints

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-10-21 22:45:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("room_inventory_prints")]

    if "is_archived" not in columns:
        op.add_column(
            'room_inventory_prints',
            sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false())
        )

    if "archived_at" not in columns:
        op.add_column(
            'room_inventory_prints',
            sa.Column('archived_at', sa.DateTime(), nullable=True)
        )

    op.create_index('idx_room_inv_print_is_archived', 'room_inventory_prints', ['is_archived'])


def downgrade() -> None:
    op.drop_index('idx_room_inv_print_is_archived', table_name='room_inventory_prints')
    op.drop_column('room_inventory_prints', 'archived_at')
    op.drop_column('room_inventory_prints', 'is_archived')
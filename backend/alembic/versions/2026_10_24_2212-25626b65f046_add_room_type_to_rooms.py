"""add_room_type_to_rooms

Revision ID: 25626b65f046
Revises: f7g8h9i0j1k2
Create Date: 2026-10-24 22:12:22.453575+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25626b65f046'
down_revision: Union[str, None] = 'f7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rooms', sa.Column('room_type', sa.String(length=20), nullable=False, server_default='room'))
    op.create_index('idx_rooms_room_type', 'rooms', ['room_type'])


def downgrade() -> None:
    op.drop_index('idx_rooms_room_type', table_name='rooms')
    op.drop_column('rooms', 'room_type')

"""add_unit_ids_to_transfer_acts

Revision ID: f7g8h9i0j1k2
Revises: e6f7g8h9i0j1
Create Date: 2026-10-24 20:15:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, None] = 'e6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Добавляем column unit_ids в transfer_acts
    if inspector.has_table('transfer_acts'):
        columns = [c["name"] for c in inspector.get_columns('transfer_acts')]
        if 'unit_ids' not in columns:
            op.add_column(
                'transfer_acts',
                sa.Column('unit_ids', sa.JSON(), nullable=False, server_default='[]')
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Удаляем column unit_ids из transfer_acts
    if inspector.has_table('transfer_acts'):
        columns = [c["name"] for c in inspector.get_columns('transfer_acts')]
        if 'unit_ids' in columns:
            op.drop_column('transfer_acts', 'unit_ids')

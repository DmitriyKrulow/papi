"""add_asset_units_table_and_update_transfer_history

Revision ID: e6f7g8h9i0j1
Revises: d5e6f7g8h9i0
Create Date: 2026-10-24 19:30:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7g8h9i0j1'
down_revision: Union[str, None] = 'd5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Создаём таблицу asset_units
    if not inspector.has_table('asset_units'):
        op.create_table(
            'asset_units',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('asset_id', sa.Integer(), nullable=False),
            sa.Column('unit_number', sa.Integer(), nullable=False),
            sa.Column('unique_identifier', sa.String(100), nullable=False),
            sa.Column('current_employee_id', sa.Integer(), nullable=True),
            sa.Column('current_department_code', sa.String(50), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='active'),
            sa.Column('last_transfer_date', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('rfid_tag', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
            sa.ForeignKeyConstraint(['current_employee_id'], ['employees.id']),
        )
        op.create_index('idx_asset_units_asset_id', 'asset_units', ['asset_id'])
        op.create_index('idx_asset_units_unique_identifier', 'asset_units', ['unique_identifier'])
        op.create_index('idx_asset_units_status', 'asset_units', ['status'])
        op.create_index('idx_asset_units_is_active', 'asset_units', ['is_active'])
        op.create_index('idx_asset_units_rfid_tag', 'asset_units', ['rfid_tag'])

    # 2. Добавляем column asset_unit_id в asset_transfer_history
    if inspector.has_table('asset_transfer_history'):
        columns = [c["name"] for c in inspector.get_columns('asset_transfer_history')]
        if 'asset_unit_id' not in columns:
            op.add_column(
                'asset_transfer_history',
                sa.Column('asset_unit_id', sa.Integer(), nullable=True)
            )
            op.create_index(
                'idx_asset_transfer_history_asset_unit_id',
                'asset_transfer_history',
                ['asset_unit_id']
            )
            op.execute(
                "ALTER TABLE asset_transfer_history "
                "ADD CONSTRAINT fk_asset_transfer_history_asset_unit_id "
                "FOREIGN KEY (asset_unit_id) REFERENCES asset_units(id)"
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Удаляем column из asset_transfer_history
    if inspector.has_table('asset_transfer_history'):
        columns = [c["name"] for c in inspector.get_columns('asset_transfer_history')]
        if 'asset_unit_id' in columns:
            op.drop_constraint(
                'fk_asset_transfer_history_asset_unit_id',
                'asset_transfer_history', type_='foreignkey'
            )
            op.drop_index('idx_asset_transfer_history_asset_unit_id', table_name='asset_transfer_history')
            op.drop_column('asset_transfer_history', 'asset_unit_id')

    # Удаляем таблицу asset_units
    if inspector.has_table('asset_units'):
        op.drop_index('idx_asset_units_rfid_tag', table_name='asset_units')
        op.drop_index('idx_asset_units_is_active', table_name='asset_units')
        op.drop_index('idx_asset_units_status', table_name='asset_units')
        op.drop_index('idx_asset_units_unique_identifier', table_name='asset_units')
        op.drop_index('idx_asset_units_asset_id', table_name='asset_units')
        op.drop_table('asset_units')

"""add_warehouse_locations_and_update_storage_addresses

Revision ID: d5e6f7g8h9i0
Revises: c4d5e6f7g8h9
Create Date: 2026-10-24 16:00:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7g8h9i0'
down_revision: Union[str, None] = 'c4d5e6f7g8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Создаём таблицу warehouse_locations
    if not inspector.has_table('warehouse_locations'):
        op.create_table(
            'warehouse_locations',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(50), nullable=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('location_type', sa.String(50), nullable=False, server_default='storage'),
            sa.Column('capacity', sa.Integer(), nullable=True),
            sa.Column('current_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id']),
        )
        op.create_index('idx_warehouse_locations_room_id', 'warehouse_locations', ['room_id'])
        op.create_index('idx_warehouse_locations_code', 'warehouse_locations', ['code'])
        op.create_index('idx_warehouse_locations_type', 'warehouse_locations', ['location_type'])
        op.create_index('idx_warehouse_locations_is_active', 'warehouse_locations', ['is_active'])

    # 2. Добавляем column warehouse_location_id в storage_addresses
    if inspector.has_table('storage_addresses'):
        columns = [c["name"] for c in inspector.get_columns('storage_addresses')]
        if 'warehouse_location_id' not in columns:
            op.add_column(
                'storage_addresses',
                sa.Column('warehouse_location_id', sa.Integer(), nullable=True)
            )
            op.create_index(
                'idx_storage_addresses_warehouse_location_id',
                'storage_addresses',
                ['warehouse_location_id']
            )
            op.execute(
                "ALTER TABLE storage_addresses "
                "ADD CONSTRAINT fk_storage_addresses_warehouse_location_id "
                "FOREIGN KEY (warehouse_location_id) REFERENCES warehouse_locations(id)"
            )

    # 3. Добавляем column warehouse_location_id в assets
    if inspector.has_table('assets'):
        columns = [c["name"] for c in inspector.get_columns('assets')]
        if 'warehouse_location_id' not in columns:
            op.add_column(
                'assets',
                sa.Column('warehouse_location_id', sa.Integer(), nullable=True)
            )
            op.create_index(
                'idx_assets_warehouse_location_id',
                'assets',
                ['warehouse_location_id']
            )
            op.execute(
                "ALTER TABLE assets "
                "ADD CONSTRAINT fk_assets_warehouse_location_id "
                "FOREIGN KEY (warehouse_location_id) REFERENCES warehouse_locations(id)"
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Удаляем columns из assets
    if inspector.has_table('assets'):
        columns = [c["name"] for c in inspector.get_columns('assets')]
        if 'warehouse_location_id' in columns:
            op.drop_constraint('fk_assets_warehouse_location_id', 'assets', type_='foreignkey')
            op.drop_index('idx_assets_warehouse_location_id', table_name='assets')
            op.drop_column('assets', 'warehouse_location_id')

    # Удаляем columns из storage_addresses
    if inspector.has_table('storage_addresses'):
        columns = [c["name"] for c in inspector.get_columns('storage_addresses')]
        if 'warehouse_location_id' in columns:
            op.drop_constraint(
                'fk_storage_addresses_warehouse_location_id',
                'storage_addresses', type_='foreignkey'
            )
            op.drop_index('idx_storage_addresses_warehouse_location_id', table_name='storage_addresses')
            op.drop_column('storage_addresses', 'warehouse_location_id')

    # Удаляем таблицу warehouse_locations
    if inspector.has_table('warehouse_locations'):
        op.drop_index('idx_warehouse_locations_is_active', table_name='warehouse_locations')
        op.drop_index('idx_warehouse_locations_type', table_name='warehouse_locations')
        op.drop_index('idx_warehouse_locations_code', table_name='warehouse_locations')
        op.drop_index('idx_warehouse_locations_room_id', table_name='warehouse_locations')
        op.drop_table('warehouse_locations')

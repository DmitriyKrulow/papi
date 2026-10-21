"""add_room_inventory_prints_table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-21 21:30:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Таблица могла быть создана автоматически через Base.metadata.create_all,
    # поэтому создаём только если её ещё нет (идемпотентно).
    if not inspector.has_table('room_inventory_prints'):
        op.create_table(
            'room_inventory_prints',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('room_name', sa.String(100), nullable=False),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('department_name', sa.String(255), nullable=True),
            sa.Column('employee_id', sa.Integer(), nullable=True),
            sa.Column('employee_name', sa.String(255), nullable=True),
            sa.Column('employee_position', sa.String(255), nullable=True),
            sa.Column('asset_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('file_path', sa.String(500), nullable=True),
            sa.Column('signed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('signed_at', sa.DateTime(), nullable=True),
            sa.Column('signed_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_by_user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id']),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
            sa.ForeignKeyConstraint(['employee_id'], ['employees.id']),
            sa.ForeignKeyConstraint(['signed_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        )

    # Индексы также создаём только отсутствующие
    existing_indexes = {
        idx["name"] for idx in inspector.get_indexes("room_inventory_prints")
    }
    index_defs = [
        ('idx_room_inv_print_room_id', ['room_id']),
        ('idx_room_inv_print_employee_id', ['employee_id']),
        ('idx_room_inv_print_signed', ['signed']),
        ('idx_room_inv_print_created_at', ['created_at']),
    ]
    for index_name, columns in index_defs:
        if index_name not in existing_indexes:
            op.create_index(index_name, 'room_inventory_prints', columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('room_inventory_prints'):
        return

    existing_indexes = {
        idx["name"] for idx in inspector.get_indexes("room_inventory_prints")
    }
    for index_name in [
        'idx_room_inv_print_created_at',
        'idx_room_inv_print_signed',
        'idx_room_inv_print_employee_id',
        'idx_room_inv_print_room_id',
    ]:
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name='room_inventory_prints')
    op.drop_table('room_inventory_prints')

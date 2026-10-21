"""add_transfer_acts_and_transfer_history

Revision ID: c4d5e6f7g8h9
Revises: c3d4e5f6g7h8
Create Date: 2026-10-21 23:00:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7g8h9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Акт передачи имущества
    if not inspector.has_table('transfer_acts'):
        op.create_table(
            'transfer_acts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('act_number', sa.String(50), nullable=False),
            sa.Column('act_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('employee_id', sa.Integer(), nullable=True),
            sa.Column('employee_name', sa.String(255), nullable=True),
            sa.Column('employee_position', sa.String(255), nullable=True),
            sa.Column('department_id', sa.Integer(), nullable=True),
            sa.Column('department_name', sa.String(255), nullable=True),
            sa.Column('room_id', sa.Integer(), nullable=True),
            sa.Column('room_name', sa.String(255), nullable=True),
            sa.Column('asset_ids', sa.JSON(), nullable=False),
            sa.Column('file_path', sa.String(500), nullable=True),
            sa.Column('attachments', sa.JSON(), nullable=False),
            sa.Column('signed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('signed_at', sa.DateTime(), nullable=True),
            sa.Column('signed_by_user_id', sa.Integer(), nullable=True),
            sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.Column('created_by_user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['employee_id'], ['employees.id']),
            sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id']),
            sa.ForeignKeyConstraint(['signed_by_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        )
        op.create_index('idx_transfer_acts_act_number', 'transfer_acts', ['act_number'])
        op.create_index('idx_transfer_acts_employee_id', 'transfer_acts', ['employee_id'])
        op.create_index('idx_transfer_acts_signed', 'transfer_acts', ['signed'])
        op.create_index('idx_transfer_acts_is_archived', 'transfer_acts', ['is_archived'])
        op.create_index('idx_transfer_acts_created_at', 'transfer_acts', ['created_at'])

    # История передач активов
    if not inspector.has_table('asset_transfer_history'):
        op.create_table(
            'asset_transfer_history',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('asset_id', sa.Integer(), nullable=False),
            sa.Column('new_employee_id', sa.Integer(), nullable=True),
            sa.Column('new_employee_name', sa.String(255), nullable=True),
            sa.Column('prev_employee_id', sa.Integer(), nullable=True),
            sa.Column('prev_employee_name', sa.String(255), nullable=True),
            sa.Column('source', sa.String(30), nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=True),
            sa.Column('source_ref', sa.String(255), nullable=True),
            sa.Column('transfer_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
            sa.ForeignKeyConstraint(['new_employee_id'], ['employees.id']),
            sa.ForeignKeyConstraint(['prev_employee_id'], ['employees.id']),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        )
        op.create_index('idx_asset_transfer_history_asset_id', 'asset_transfer_history', ['asset_id'])
        op.create_index('idx_asset_transfer_history_new_employee_id', 'asset_transfer_history', ['new_employee_id'])
        op.create_index('idx_asset_transfer_history_source', 'asset_transfer_history', ['source'])
        op.create_index('idx_asset_transfer_history_transfer_date', 'asset_transfer_history', ['transfer_date'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('asset_transfer_history'):
        op.drop_index('idx_asset_transfer_history_transfer_date', table_name='asset_transfer_history')
        op.drop_index('idx_asset_transfer_history_source', table_name='asset_transfer_history')
        op.drop_index('idx_asset_transfer_history_new_employee_id', table_name='asset_transfer_history')
        op.drop_index('idx_asset_transfer_history_asset_id', table_name='asset_transfer_history')
        op.drop_table('asset_transfer_history')

    if inspector.has_table('transfer_acts'):
        op.drop_index('idx_transfer_acts_created_at', table_name='transfer_acts')
        op.drop_index('idx_transfer_acts_is_archived', table_name='transfer_acts')
        op.drop_index('idx_transfer_acts_signed', table_name='transfer_acts')
        op.drop_index('idx_transfer_acts_employee_id', table_name='transfer_acts')
        op.drop_index('idx_transfer_acts_act_number', table_name='transfer_acts')
        op.drop_table('transfer_acts')
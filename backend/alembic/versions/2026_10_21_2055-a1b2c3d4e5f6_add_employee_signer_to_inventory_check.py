"""add_employee_signer_to_inventory_check

Revision ID: a1b2c3d4e5f6
Revises: d9ba1cc62ea8
Create Date: 2026-10-21 20:00:00.000000+03:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd9ba1cc62ea8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("inventory_checks")]
    
    if "employee_id" not in columns:
        op.add_column('inventory_checks', 
            sa.Column('employee_id', sa.Integer(), nullable=True)
        )
        op.create_foreign_key(
            'fk_inventory_checks_employee_id_employees',
            'inventory_checks', 'employees',
            ['employee_id'], ['id']
        )
    
    if "employee_name" not in columns:
        op.add_column('inventory_checks', 
            sa.Column('employee_name', sa.String(255), nullable=True)
        )
    
    if "employee_position" not in columns:
        op.add_column('inventory_checks', 
            sa.Column('employee_position', sa.String(255), nullable=True)
        )


def downgrade() -> None:
    op.drop_column('inventory_checks', 'employee_position')
    op.drop_column('inventory_checks', 'employee_name')
    op.drop_column('inventory_checks', 'employee_id')

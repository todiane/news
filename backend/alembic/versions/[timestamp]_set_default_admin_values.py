"""set default admin values

Revision ID: set_default_admin_values
Revises: ee4733fbcdfd
Create Date: 2025-01-28 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'set_default_admin_values'
down_revision: Union[str, None] = 'ee4733fbcdfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Set default value for existing records
    op.execute("UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL")
    
    # Make the column non-nullable
    op.alter_column('users', 'is_admin',
               existing_type=sa.Boolean(),
               nullable=False,
               server_default=sa.text('0'))

def downgrade() -> None:
    op.alter_column('users', 'is_admin',
               existing_type=sa.Boolean(),
               nullable=True,
               server_default=None)
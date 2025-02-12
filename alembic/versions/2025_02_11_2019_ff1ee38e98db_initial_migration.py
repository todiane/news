"""initial migration

Revision ID: ff1ee38e98db
Revises: 79b847e5ec91
Create Date: 2025-02-11 20:19:04.168256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff1ee38e98db'
down_revision: Union[str, None] = '79b847e5ec91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
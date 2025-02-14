"""create initial tables

Revision ID: 86eaf1c243cd
Revises: ff1ee38e98db
Create Date: 2025-02-14 11:20:12.708509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86eaf1c243cd'
down_revision: Union[str, None] = 'ff1ee38e98db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
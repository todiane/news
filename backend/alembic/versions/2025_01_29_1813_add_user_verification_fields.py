"""add user verification fields

Revision ID: add_user_verification_fields
Revises: 1ce9cffedf6a
Create Date: 2025-01-29 18:13:45.711110

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'add_user_verification_fields'
down_revision: Union[str, None] = '1ce9cffedf6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('verification_sent_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE users SET is_verified = FALSE WHERE is_verified IS NULL")

def downgrade() -> None:
    # Remove the new columns
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'verification_sent_at')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'password_reset_at')
    op.drop_column('users', 'last_login')
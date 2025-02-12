from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os

# this is the Alembic Config object
config = context.config

# Read database URL from environment variable
def get_url():
    return os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")

# Set SQLAlchemy URL in alembic
config.set_main_option("sqlalchemy.url", get_url())

# Import all the models here for Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.article import Article  # noqa
from app.models.feed import Feed  # noqa
from app.models.feed_history import FeedHistory  # noqa
from app.models.feed_preference import FeedPreference  # noqa

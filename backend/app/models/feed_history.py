# backend/app/models/feed_history.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class FeedHistory(Base):
    __tablename__ = "feed_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    
    # Reading status
    read_at = Column(DateTime, nullable=True)
    last_position = Column(Float, nullable=True)  # For tracking scroll position
    read_duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # First view and last view timestamps
    first_viewed_at = Column(DateTime, default=datetime.utcnow)
    last_viewed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feed_history")
    article = relationship("Article", back_populates="read_history")
    feed = relationship("Feed", back_populates="read_history")
    
    # Add indexes for efficient querying
    __table_args__ = (
        Index('idx_feed_history_user_article', user_id, article_id, unique=True),
        Index('idx_feed_history_user_feed', user_id, feed_id),
        Index('idx_feed_history_read_status', user_id, read_at.is_(None)),
    )

    def mark_as_read(self, position: float = None, duration: int = None):
        """Mark the article as read with optional position and duration."""
        if not self.read_at:  # Only update if not already marked as read
            self.read_at = datetime.utcnow()
            if position is not None:
                self.last_position = position
            if duration is not None:
                self.read_duration = duration
        
        self.last_viewed_at = datetime.utcnow()

    def update_progress(self, position: float, duration: int = None):
        """Update reading progress without marking as complete."""
        self.last_position = position
        if duration is not None:
            self.read_duration = duration
        self.last_viewed_at = datetime.utcnow()

    @property
    def is_read(self) -> bool:
        """Check if the article has been read."""
        return self.read_at is not None
    
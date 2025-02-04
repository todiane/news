# backend/app/models/feed_preference.py

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class FeedPreference(Base):
    __tablename__ = "feed_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    
    # Subscription settings
    is_favorite = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=True)
    update_frequency = Column(String(20), default="realtime")  # realtime, hourly, daily, weekly
    categories = Column(JSON)  # Custom categories/tags
    
    # Reading status
    last_read_at = Column(DateTime, nullable=True)
    read_items = Column(JSON, default=dict)  # Store read article IDs
    bookmarked_items = Column(JSON, default=dict)  # Store bookmarked article IDs
    
    # Relationships
    user = relationship("User", back_populates="feed_preferences")
    feed = relationship("Feed", back_populates="user_preferences")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

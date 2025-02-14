from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON  # Add JSON here
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(512), nullable=False)
    feed_type = Column(String(50), nullable=False)  # 'rss', 'youtube'
    category = Column(String(50))
    extra_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="feeds")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_preferences = relationship("FeedPreference", back_populates="feed")
    read_history = relationship("FeedHistory", back_populates="feed")
    
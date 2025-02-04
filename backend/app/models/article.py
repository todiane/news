from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(512), nullable=False)
    source = Column(String(100), nullable=False)
    source_id = Column(String(100))
    api_source = Column(String(50))
    category = Column(String(50))
    author = Column(String(100))
    extra_data = Column(JSON)  
    published_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    read_history = relationship("FeedHistory", back_populates="article")
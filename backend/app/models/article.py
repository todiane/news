# backend/app/models/article.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(512), nullable=False)
    source = Column(String(100), nullable=False)
    published_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

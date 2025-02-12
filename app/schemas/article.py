from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

# Base Article Schema (shared properties)
class ArticleBase(BaseModel):
    title: str
    content: str
    url: HttpUrl
    source: str

# Schema for creating Article
class ArticleCreate(ArticleBase):
    pass

# Schema for updating Article
class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[HttpUrl] = None
    source: Optional[str] = None

# Schema for Article in DB
class Article(ArticleBase):
    id: int
    published_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
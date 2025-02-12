from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class FeedBase(BaseModel):
    name: str
    url: HttpUrl
    feed_type: str
    category: Optional[str] = None

class FeedCreate(FeedBase):
    pass

class FeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    feed_type: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Feed(FeedBase):
    id: int
    is_active: bool
    user_id: int
    last_fetched: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
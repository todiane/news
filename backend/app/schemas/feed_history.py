# backend/app/schemas/feed_history.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FeedHistoryBase(BaseModel):
    item_id: str
    source_type: str = Field(..., description="Type of content - 'article' or 'video'")
    read_status: bool = False
    progress: int = Field(0, ge=0, le=100, description="Reading progress percentage")

class FeedHistoryCreate(FeedHistoryBase):
    user_id: int
    feed_id: int

class FeedHistoryUpdate(BaseModel):
    read_status: Optional[bool] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    last_read: Optional[datetime] = None

class FeedHistory(FeedHistoryBase):
    id: int
    user_id: int
    feed_id: int
    created_at: datetime
    last_read: Optional[datetime]

    class Config:
        from_attributes = True
        
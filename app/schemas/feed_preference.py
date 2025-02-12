# app/schemas/feed_preference.py

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class FeedPreferenceBase(BaseModel):
    is_favorite: bool = False
    notification_enabled: bool = True
    update_frequency: str = "realtime"
    categories: Optional[List[str]] = []

class FeedPreferenceCreate(FeedPreferenceBase):
    feed_id: int

class FeedPreferenceUpdate(FeedPreferenceBase):
    pass

class FeedPreference(FeedPreferenceBase):
    id: int
    user_id: int
    feed_id: int
    last_read_at: Optional[datetime]
    read_items: Dict[str, datetime] = {}
    bookmarked_items: Dict[str, datetime] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
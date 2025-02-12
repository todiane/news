from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_  
from app.crud.base import CRUDBase
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate
from datetime import datetime


class CRUDFeed(CRUDBase[Feed, FeedCreate, FeedUpdate]):
    def get_by_url(self, db: Session, *, url: str) -> Optional[Feed]:
        return db.query(Feed).filter(Feed.url == url).first()
    
    def get_user_feeds(self, db: Session, *, user_id: int) -> List[Feed]:
        return db.query(Feed).filter(Feed.user_id == user_id).all()
    
    def get_active_feeds(self, db: Session) -> List[Feed]:
        return db.query(Feed).filter(Feed.is_active == True).all()
    
    async def update_feed_content(self, db: Session, feed_id: int, content: List[Dict[str, Any]]) -> Feed:
        """Update feed content."""
        feed = self.get(db, id=feed_id)
        if feed:
            feed.last_fetched = datetime.utcnow()
            feed.extra_data = {"last_content": content}
            db.commit()
            db.refresh(feed)
        return feed
    
    async def get_feeds_needing_refresh(self, threshold: datetime):
        """Get feeds that need refreshing."""
        return (
            self.model.query
            .filter(
                or_(
                    self.model.last_fetched.is_(None),
                    self.model.last_fetched <= threshold
                )
            )
            .filter(self.model.is_active.is_(True))
            .all()
        )

feed = CRUDFeed(Feed)
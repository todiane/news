from typing import List, Optional
from sqlalchemy.orm import Session
from ..crud.base import CRUDBase
from ..models.feed import Feed
from ..schemas.feed import FeedCreate, FeedUpdate

class CRUDFeed(CRUDBase[Feed, FeedCreate, FeedUpdate]):
    def get_by_url(self, db: Session, *, url: str) -> Optional[Feed]:
        return db.query(Feed).filter(Feed.url == url).first()
    
    def get_user_feeds(self, db: Session, *, user_id: int) -> List[Feed]:
        return db.query(Feed).filter(Feed.user_id == user_id).all()
    
    def get_active_feeds(self, db: Session) -> List[Feed]:
        return db.query(Feed).filter(Feed.is_active == True).all()

feed = CRUDFeed(Feed)
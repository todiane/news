from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi.encoders import jsonable_encoder
from app.crud.base import CRUDBase
from app.models.feed_history import FeedHistory
from app.schemas.feed_history import FeedHistoryCreate, FeedHistoryUpdate

class CRUDFeedHistory(CRUDBase[FeedHistory, FeedHistoryCreate, FeedHistoryUpdate]):
    def get_by_user_and_article(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        article_id: int
    ) -> Optional[FeedHistory]:
        """Get history record for specific user and article."""
        return db.query(FeedHistory).filter(
            FeedHistory.user_id == user_id,
            FeedHistory.article_id == article_id
        ).first()

    def get_user_history(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[FeedHistory]:
        """Get all history records for a user."""
        return db.query(FeedHistory)\
            .filter(FeedHistory.user_id == user_id)\
            .order_by(FeedHistory.last_viewed_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_feed_history(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        feed_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[FeedHistory]:
        """Get history records for a specific feed."""
        return db.query(FeedHistory)\
            .filter(
                FeedHistory.user_id == user_id,
                FeedHistory.feed_id == feed_id
            )\
            .order_by(FeedHistory.last_viewed_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def mark_as_read(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        article_id: int,
        position: Optional[float] = None,
        duration: Optional[int] = None
    ) -> FeedHistory:
        """Mark an article as read with optional position and duration."""
        history = self.get_by_user_and_article(db, user_id=user_id, article_id=article_id)
        if not history:
            return None
        
        history.mark_as_read(position=position, duration=duration)
        db.commit()
        db.refresh(history)
        return history

    def update_progress(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        article_id: int,
        position: float,
        duration: Optional[int] = None
    ) -> FeedHistory:
        """Update reading progress for an article."""
        history = self.get_by_user_and_article(db, user_id=user_id, article_id=article_id)
        if not history:
            return None
            
        history.update_progress(position=position, duration=duration)
        db.commit()
        db.refresh(history)
        return history

    def get_unread_articles(
        self, 
        db: Session, 
        *, 
        user_id: int,
        feed_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[FeedHistory]:
        """Get unread articles for a user, optionally filtered by feed."""
        query = db.query(FeedHistory).filter(
            FeedHistory.user_id == user_id,
            FeedHistory.read_at.is_(None)
        )
        
        if feed_id:
            query = query.filter(FeedHistory.feed_id == feed_id)
            
        return query.order_by(FeedHistory.first_viewed_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_reading_stats(
        self, 
        db: Session, 
        *, 
        user_id: int,
        feed_id: Optional[int] = None,
        days: int = 30
    ) -> dict:
        """Get reading statistics for a user."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        query = db.query(FeedHistory).filter(
            FeedHistory.user_id == user_id,
            FeedHistory.last_viewed_at >= since_date
        )
        
        if feed_id:
            query = query.filter(FeedHistory.feed_id == feed_id)
        
        # Calculate statistics
        stats = {
            "total_articles": query.count(),
            "articles_read": query.filter(FeedHistory.read_at.isnot(None)).count(),
            "total_reading_time": query.with_entities(
                func.sum(FeedHistory.read_duration)
            ).scalar() or 0,
            "average_completion": query.with_entities(
                func.avg(FeedHistory.last_position)
            ).scalar() or 0
        }
        
        # Calculate reading streak
        streak = 0
        current_date = datetime.utcnow().date()
        
        while True:
            day_has_activity = db.query(FeedHistory).filter(
                FeedHistory.user_id == user_id,
                func.date(FeedHistory.last_viewed_at) == current_date
            ).first() is not None
            
            if not day_has_activity:
                break
                
            streak += 1
            current_date -= timedelta(days=1)
        
        stats["current_streak"] = streak
        return stats

    def bulk_create_or_update(
        self,
        db: Session,
        *,
        user_id: int,
        items: List[FeedHistoryCreate]
    ) -> List[FeedHistory]:
        """Bulk create or update history records."""
        history_records = []
        
        for item in items:
            existing = self.get_by_user_and_article(
                db, 
                user_id=user_id, 
                article_id=item.article_id
            )
            
            if existing:
                # Update existing record
                obj_data = jsonable_encoder(existing)
                update_data = item.dict(exclude_unset=True)
                for field in obj_data:
                    if field in update_data:
                        setattr(existing, field, update_data[field])
                history_records.append(existing)
            else:
                # Create new record
                db_obj = FeedHistory(
                    user_id=user_id,
                    **item.dict(exclude={'user_id'})
                )
                db.add(db_obj)
                history_records.append(db_obj)
        
        db.commit()
        for record in history_records:
            db.refresh(record)
            
        return history_records

feed_history = CRUDFeedHistory(FeedHistory)

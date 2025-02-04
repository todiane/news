from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.crud.feed_history import feed_history
from app.schemas.feed_history import FeedHistory, FeedHistoryCreate, FeedHistoryUpdate

router = APIRouter(prefix="/feed-history", tags=["feed-history"])

@router.get("/", response_model=List[FeedHistory])
async def get_reading_history(
    skip: int = 0,
    limit: int = 100,
    feed_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's reading history, optionally filtered by feed."""
    if feed_id:
        return feed_history.get_feed_history(
            db, user_id=current_user.id, feed_id=feed_id, skip=skip, limit=limit
        )
    return feed_history.get_user_history(
        db, user_id=current_user.id, skip=skip, limit=limit
    )

@router.post("/{article_id}/read")
async def mark_as_read(
    article_id: int,
    position: Optional[float] = None,
    duration: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an article as read with optional position and duration."""
    result = feed_history.mark_as_read(
        db, 
        user_id=current_user.id, 
        article_id=article_id,
        position=position,
        duration=duration
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found in history"
        )
    return {"status": "success"}

@router.post("/{article_id}/progress")
async def update_reading_progress(
    article_id: int,
    position: float,
    duration: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update reading progress for an article."""
    result = feed_history.update_progress(
        db,
        user_id=current_user.id,
        article_id=article_id,
        position=position,
        duration=duration
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found in history"
        )
    return {"status": "success"}

@router.get("/unread")
async def get_unread_articles(
    skip: int = 0,
    limit: int = 100,
    feed_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's unread articles."""
    return feed_history.get_unread_articles(
        db,
        user_id=current_user.id,
        feed_id=feed_id,
        skip=skip,
        limit=limit
    )

@router.get("/stats")
async def get_reading_stats(
    days: int = 30,
    feed_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reading statistics for the user."""
    return feed_history.get_reading_stats(
        db,
        user_id=current_user.id,
        feed_id=feed_id,
        days=days
    )

@router.post("/bulk-update")
async def bulk_update_history(
    items: List[FeedHistoryCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk create or update history records."""
    return feed_history.bulk_create_or_update(
        db,
        user_id=current_user.id,
        items=items
    )

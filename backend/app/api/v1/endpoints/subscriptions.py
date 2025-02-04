# backend/app/api/v1/endpoints/subscriptions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.feed_preference import FeedPreference
from app.schemas.feed_preference import (
    FeedPreference as FeedPreferenceSchema,
    FeedPreferenceCreate,
    FeedPreferenceUpdate
)

router = APIRouter()

@router.post("/preferences", response_model=FeedPreferenceSchema)
async def create_feed_preference(
    preference_in: FeedPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new feed preference settings."""
    existing = db.query(FeedPreference).filter(
        FeedPreference.user_id == current_user.id,
        FeedPreference.feed_id == preference_in.feed_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Preferences already exist for this feed"
        )
    
    db_pref = FeedPreference(
        user_id=current_user.id,
        **preference_in.dict()
    )
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

@router.get("/preferences", response_model=List[FeedPreferenceSchema])
async def get_feed_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all feed preferences for current user."""
    return db.query(FeedPreference).filter(
        FeedPreference.user_id == current_user.id
    ).all()

@router.put("/preferences/{feed_id}", response_model=FeedPreferenceSchema)
async def update_feed_preference(
    feed_id: int,
    preference_in: FeedPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feed preferences."""
    db_pref = db.query(FeedPreference).filter(
        FeedPreference.user_id == current_user.id,
        FeedPreference.feed_id == feed_id
    ).first()
    
    if not db_pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    for field, value in preference_in.dict(exclude_unset=True).items():
        setattr(db_pref, field, value)
    
    db.commit()
    db.refresh(db_pref)
    return db_pref

@router.post("/preferences/{feed_id}/read/{article_id}")
async def mark_article_read(
    feed_id: int,
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an article as read."""
    db_pref = db.query(FeedPreference).filter(
        FeedPreference.user_id == current_user.id,
        FeedPreference.feed_id == feed_id
    ).first()
    
    if not db_pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    read_items = db_pref.read_items or {}
    read_items[article_id] = datetime.utcnow().isoformat()
    db_pref.read_items = read_items
    db_pref.last_read_at = datetime.utcnow()
    
    db.commit()
    return {"status": "success"}

@router.post("/preferences/{feed_id}/bookmark/{article_id}")
async def toggle_bookmark(
    feed_id: int,
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle bookmark status for an article."""
    db_pref = db.query(FeedPreference).filter(
        FeedPreference.user_id == current_user.id,
        FeedPreference.feed_id == feed_id
    ).first()
    
    if not db_pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    bookmarked_items = db_pref.bookmarked_items or {}
    if article_id in bookmarked_items:
        del bookmarked_items[article_id]
    else:
        bookmarked_items[article_id] = datetime.utcnow().isoformat()
    
    db_pref.bookmarked_items = bookmarked_items
    db.commit()
    return {"status": "success", "bookmarked": article_id in bookmarked_items}

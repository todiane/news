from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=FeedSchema)
def create_feed(
    feed_in: FeedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feed = Feed(
        **feed_in.dict(),
        user_id=current_user.id
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed

@router.get("/my-feeds", response_model=List[FeedSchema])
def get_my_feeds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Feed).filter(Feed.user_id == current_user.id).all()

@router.put("/{feed_id}", response_model=FeedSchema)
def update_feed(
    feed_id: int,
    feed_in: FeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    for field, value in feed_in.dict(exclude_unset=True).items():
        setattr(feed, field, value)
    
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed

@router.delete("/{feed_id}")
def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(feed)
    db.commit()
    return {"ok": True}
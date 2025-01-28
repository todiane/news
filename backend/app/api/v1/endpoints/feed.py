from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.schemas.article import Article
from app.core.auth import get_current_user
from app.models.user import User
from app.core.feed_fetcher import fetch_all_feeds
from app.crud.article import article as article_crud
from app.core.cache_manager import CacheWarmer
from app.core.cache import CacheManager

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

@router.post("/cache/warm/{feed_id}")
async def warm_feed_cache(
    feed_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger cache warming for a specific feed.
    """
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    cache_warmer = CacheWarmer(db)
    await cache_warmer.start_warming(background_tasks)
    return {"message": "Cache warming started"}

@router.post("/cache/invalidate/{feed_id}")
async def invalidate_feed_cache(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Force invalidate cache for a specific feed.
    """
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    cache_warmer = CacheWarmer(db)
    success = await cache_warmer.force_invalidate(feed.url)
    
    return {
        "message": "Cache invalidated",
        "rewarmed": success
    }

@router.get("/cache/stats")
async def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cache statistics and metrics.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Only admins can view cache stats"
        )
    
    cache_warmer = CacheWarmer(db)
    cache_stats = cache_warmer.get_warming_stats()
    
    # Get Redis stats if available
    cache_manager = CacheManager()
    redis_stats = cache_manager.get_stats()
    
    return {
        "warming_stats": cache_stats,
        "redis_stats": redis_stats
    }

# New endpoints that use caching system

@router.get("/refresh", response_model=List[Article])
async def refresh_feeds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refresh and return articles from all feeds for the current user.
    Uses caching to prevent excessive API calls.
    """
    # Get user's feed URLs from database
    user_feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
    feed_urls = [feed.url for feed in user_feeds]
    
    if not feed_urls:
        return []
    
    # Fetch articles from all feeds (cached)
    articles = await fetch_all_feeds(feed_urls)
    
    # Save new articles to database
    saved_articles = []
    for article_data in articles:
        # Check if article already exists
        existing = article_crud.get_by_url(db, url=article_data["url"])
        if not existing:
            # Create new article
            new_article = article_crud.create(db, obj_in=article_data)
            saved_articles.append(new_article)
    
    return saved_articles

@router.get("/articles", response_model=List[Article])
def get_feed_articles(
    skip: int = 0,
    limit: int = 100,
    feed_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cached articles from database, optionally filtered by feed_id.
    """
    query = db.query(article_crud.model)
    
    if feed_id:
        # Verify feed belongs to user
        feed = db.query(Feed).filter(
            Feed.id == feed_id,
            Feed.user_id == current_user.id
        ).first()
        if not feed:
            raise HTTPException(status_code=404, detail="Feed not found")
        query = query.filter(article_crud.model.feed_id == feed_id)
    else:
        # Get articles from all user's feeds
        user_feeds = db.query(Feed).filter(Feed.user_id == current_user.id)
        feed_ids = [feed.id for feed in user_feeds]
        query = query.filter(article_crud.model.feed_id.in_(feed_ids))
    
    return query.offset(skip).limit(limit).all()
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks 
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.base import get_db
from app.models.user import User
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.schemas.article import Article
from app.core.auth import get_current_user
from app.core.feed_fetcher import fetch_all_feeds
from app.crud.article import article as article_crud
from app.core.cache_manager import CacheWarmer
from app.core.cache import CacheManager
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.core.deps import get_current_user
from app.core.feed_fetcher import FeedFetcher
from app.services.feed_validator import FeedValidator

router = APIRouter()

@router.post("/validate-url")
async def validate_feed_url(
    url: str,
    feed_type: str = 'rss',
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate a feed URL before adding it.
    Returns validation status and any error messages.
    """
    async with FeedValidator() as validator:
        is_valid, error_message = await validator.validate_feed(url, feed_type)
        
        # Check if URL already exists for this user
        if is_valid:
            existing_feed = db.query(Feed).filter(
                Feed.url == url,
                Feed.user_id == current_user.id
            ).first()
            
            if existing_feed:
                return {
                    "valid": False,
                    "error": "You have already added this feed"
                }
        
        return {
            "valid": is_valid,
            "error": error_message
        }

@router.post("/", response_model=FeedSchema)
async def create_feed(
    feed_in: FeedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new feed for the current user."""
    # Validate feed URL
    async with FeedValidator() as validator:
        is_valid, error_message = await validator.validate_feed(
            feed_in.url, 
            feed_in.feed_type
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
    
    # Check for duplicate feed
    existing_feed = db.query(Feed).filter(
        Feed.url == feed_in.url,
        Feed.user_id == current_user.id
    ).first()
    
    if existing_feed:
        raise HTTPException(
            status_code=400,
            detail="You have already added this feed"
        )

    # Create new feed
    feed = Feed(
        name=feed_in.name,
        url=feed_in.url,
        category=feed_in.category,
        feed_type=feed_in.feed_type,
        user_id=current_user.id,
        is_active=True
    )
    
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed

@router.put("/{feed_id}", response_model=FeedSchema)
async def update_feed(
    feed_id: int,
    feed_in: FeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a feed."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Validate new URL if it's being updated
    if feed_in.url and feed_in.url != feed.url:
        async with FeedValidator() as validator:
            is_valid, error_message = await validator.validate_feed(
                feed_in.url,
                feed_in.feed_type or feed.feed_type
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=error_message
                )
            
            # Check for duplicate feed
            existing_feed = db.query(Feed).filter(
                Feed.url == feed_in.url,
                Feed.user_id == current_user.id,
                Feed.id != feed_id
            ).first()
            
            if existing_feed:
                raise HTTPException(
                    status_code=400,
                    detail="You have already added this feed"
                )
    
    # Update feed attributes
    for field, value in feed_in.dict(exclude_unset=True).items():
        setattr(feed, field, value)
    
    db.commit()
    db.refresh(feed)
    return feed


@router.get("/my-feeds", response_model=List[FeedSchema])
async def get_my_feeds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all feeds for the current user."""
    return db.query(Feed).filter(Feed.user_id == current_user.id).all()

@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a feed."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted successfully"}

@router.post("/refresh/{feed_id}")
async def refresh_feed(
    feed_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh a feed's content."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Add feed refresh task to background tasks
    background_tasks.add_task(refresh_feed_content, feed, db)
    
    return {"message": "Feed refresh started"}

async def refresh_feed_content(feed: Feed, db: Session):
    """Background task to refresh feed content."""
    feed_fetcher = FeedFetcher()
    try:
        # Fetch and process feed content
        await feed_fetcher.fetch_and_save_feed(feed, db)
        
        # Update last_fetched timestamp
        feed.last_fetched = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        print(f"Error refreshing feed {feed.id}: {str(e)}")
        # Log error but don't raise exception since this is a background task

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
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.core.deps import get_current_user
from app.core.feed_validator import feed_validator
from app.models.user import User
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.core.cache import CacheManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/feeds", response_model=FeedSchema)
async def create_feed(
    feed_in: FeedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new feed with validation."""
    async with feed_validator as validator:
        # Validate the feed URL
        is_valid, validation_result = await validator.validate_feed(feed_in.url)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid feed",
                    "validation_errors": validation_result
                }
            )
        
        # Create feed with validated metadata
        feed = Feed(
            name=feed_in.name or validation_result["metadata"]["title"],
            url=feed_in.url,
            feed_type=validation_result["format"],
            category=feed_in.category,
            user_id=current_user.id,
            last_fetched=datetime.utcnow(),
            extra_data=validation_result["metadata"]
        )
        
        try:
            db.add(feed)
            db.commit()
            db.refresh(feed)
            return feed
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating feed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating feed"
            )

@router.get("/feeds", response_model=List[FeedSchema])
async def get_feeds(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's feeds with optional category filter."""
    query = db.query(Feed).filter(Feed.user_id == current_user.id)
    
    if category:
        query = query.filter(Feed.category == category)
    
    feeds = query.offset(skip).limit(limit).all()
    return feeds

@router.get("/feeds/{feed_id}", response_model=FeedSchema)
async def get_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific feed."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )
    return feed

@router.put("/feeds/{feed_id}", response_model=FeedSchema)
async def update_feed(
    feed_id: int,
    feed_in: FeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a feed with validation if URL changes."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )

    # If URL is being updated, validate the new URL
    if feed_in.url and feed_in.url != feed.url:
        async with feed_validator as validator:
            is_valid, validation_result = await validator.validate_feed(feed_in.url)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Invalid feed URL",
                        "validation_errors": validation_result
                    }
                )
            
            feed.url = feed_in.url
            feed.feed_type = validation_result["format"]
            feed.extra_data = validation_result["metadata"]

    # Update other fields
    if feed_in.name:
        feed.name = feed_in.name
    if feed_in.category:
        feed.category = feed_in.category

    try:
        db.commit()
        db.refresh(feed)
        return feed
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating feed"
        )

@router.delete("/feeds/{feed_id}")
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )

    try:
        db.delete(feed)
        db.commit()
        
        # Clear any cached data for this feed
        cache = CacheManager()
        cache.invalidate(f"feed_{feed_id}")
        
        return {"message": "Feed deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting feed"
        )

@router.post("/feeds/discover")
async def discover_feed(
    website_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Discover RSS/Atom feed URL from a website URL."""
    try:
        async with feed_validator as validator:
            feed_url = await validator.discover_feed_url(website_url)
            
            if not feed_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No feed found at the provided URL"
                )
            
            # Validate discovered feed
            is_valid, validation_result = await validator.validate_feed(feed_url)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Discovered feed is invalid",
                        "validation_errors": validation_result
                    }
                )
            
            return {
                "feed_url": feed_url,
                "metadata": validation_result["metadata"],
                "format": validation_result["format"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error discovering feed"
        )

@router.post("/feeds/validate")
async def validate_feed_url(
    url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a feed URL before adding it."""
    try:
        async with feed_validator as validator:
            is_valid, validation_result = await validator.validate_feed(url)
            
            if not is_valid:
                return {
                    "is_valid": False,
                    "errors": validation_result
                }
            
            return {
                "is_valid": True,
                "metadata": validation_result["metadata"],
                "format": validation_result["format"],
                "stats": validation_result["stats"]
            }
            
    except Exception as e:
        logger.error(f"Error validating feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating feed"
        )

@router.post("/feeds/{feed_id}/refresh")
async def refresh_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh a feed."""
    feed = db.query(Feed).filter(
        Feed.id == feed_id,
        Feed.user_id == current_user.id
    ).first()
    
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )

    try:
        async with feed_validator as validator:
            is_valid, validation_result = await validator.validate_feed(feed.url)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Feed has become invalid",
                        "validation_errors": validation_result
                    }
                )
            
            # Update feed metadata
            feed.last_fetched = datetime.utcnow()
            feed.extra_data = validation_result["metadata"]
            
            db.commit()
            db.refresh(feed)
            
            # Clear cache for this feed
            cache = CacheManager()
            cache.invalidate(f"feed_{feed_id}")
            
            return {
                "message": "Feed refreshed successfully",
                "metadata": validation_result["metadata"],
                "stats": validation_result["stats"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error refreshing feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing feed"
        )

@router.get("/feeds/stats")
async def get_feed_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about user's feeds."""
    try:
        feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
        
        total_feeds = len(feeds)
        feeds_by_category = {}
        feeds_by_type = {}
        total_inactive = 0
        
        for feed in feeds:
            # Count by category
            category = feed.category or "uncategorized"
            feeds_by_category[category] = feeds_by_category.get(category, 0) + 1
            
            # Count by feed type
            feed_type = feed.feed_type or "unknown"
            feeds_by_type[feed_type] = feeds_by_type.get(feed_type, 0) + 1
            
            # Check activity
            if feed.last_fetched:
                time_diff = datetime.utcnow() - feed.last_fetched
                if time_diff.days > 7:  # Consider inactive if not fetched in 7 days
                    total_inactive += 1
        
        return {
            "total_feeds": total_feeds,
            "feeds_by_category": feeds_by_category,
            "feeds_by_type": feeds_by_type,
            "total_inactive": total_inactive,
            "active_feeds": total_feeds - total_inactive
        }
        
    except Exception as e:
        logger.error(f"Error getting feed stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving feed statistics"
        )

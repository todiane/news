from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate, Feed as FeedSchema
from app.schemas.article import Article
from app.core.deps import get_current_user
from app.models.user import User
from app.core.feed_fetcher import fetch_all_feeds
from app.crud.article import article as article_crud
from app.core.cache_manager import CacheWarmer
from app.core.cache import CacheManager
from app.core.versioning import version_config, APIVersion, VersionedResponse
from app.core.error_handler import ErrorDetail
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class FeedResponse(VersionedResponse):
    data: List[FeedSchema]
    total: int = 0

class FeedDetailResponse(VersionedResponse):
    data: FeedSchema

@router.post("/", response_model=FeedDetailResponse)
async def create_feed(
    feed_in: FeedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """
    Create a new feed.
    
    Version changes:
    - 1.0: Base implementation
    - 1.1: Added automatic feed validation
    - 2.0: Added feed categorization
    """
    try:
        feed = Feed(
            **feed_in.dict(),
            user_id=current_user.id
        )
        db.add(feed)
        db.commit()
        db.refresh(feed)
        
        return FeedDetailResponse(
            version=api_version,
            data=feed
        )
    except Exception as e:
        logger.error(f"Error creating feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="FEED_CREATE_ERROR",
                message="Failed to create feed",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.get("/my-feeds", response_model=FeedResponse)
async def get_my_feeds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Get all feeds for the current user."""
    try:
        feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
        return FeedResponse(
            version=api_version,
            data=feeds,
            total=len(feeds)
        )
    except Exception as e:
        logger.error(f"Error retrieving feeds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="FEED_FETCH_ERROR",
                message="Failed to retrieve feeds",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.put("/{feed_id}", response_model=FeedDetailResponse)
async def update_feed(
    feed_id: int,
    feed_in: FeedUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Update an existing feed."""
    try:
        feed = db.query(Feed).filter(
            Feed.id == feed_id,
            Feed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="FEED_NOT_FOUND",
                    message="Feed not found",
                    details={"id": feed_id} if version_config.is_supported(api_version) else None
                ).dict()
            )
        
        for field, value in feed_in.dict(exclude_unset=True).items():
            setattr(feed, field, value)
        
        db.add(feed)
        db.commit()
        db.refresh(feed)
        
        return FeedDetailResponse(
            version=api_version,
            data=feed
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feed {feed_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="FEED_UPDATE_ERROR",
                message="Failed to update feed",
                details={"id": feed_id} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Delete a feed."""
    try:
        feed = db.query(Feed).filter(
            Feed.id == feed_id,
            Feed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="FEED_NOT_FOUND",
                    message="Feed not found",
                    details={"id": feed_id} if version_config.is_supported(api_version) else None
                ).dict()
            )
        
        db.delete(feed)
        db.commit()
        
        return {
            "version": api_version,
            "message": "Feed deleted successfully",
            "id": feed_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feed {feed_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="FEED_DELETE_ERROR",
                message="Failed to delete feed",
                details={"id": feed_id} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.get("/refresh", response_model=List[Article])
async def refresh_feeds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Refresh and return articles from all feeds for the current user."""
    try:
        user_feeds = db.query(Feed).filter(Feed.user_id == current_user.id).all()
        feed_urls = [feed.url for feed in user_feeds]
        
        if not feed_urls:
            return []
        
        articles = await fetch_all_feeds(feed_urls)
        
        # Save new articles
        saved_articles = []
        for article_data in articles:
            existing = article_crud.get_by_url(db, url=article_data["url"])
            if not existing:
                new_article = article_crud.create(db, obj_in=article_data)
                saved_articles.append(new_article)
        
        return saved_articles
    except Exception as e:
        logger.error(f"Error refreshing feeds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="FEED_REFRESH_ERROR",
                message="Failed to refresh feeds",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("/cache/warm/{feed_id}")
async def warm_feed_cache(
    feed_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Manually trigger cache warming for a specific feed."""
    try:
        feed = db.query(Feed).filter(
            Feed.id == feed_id,
            Feed.user_id == current_user.id
        ).first()
        
        if not feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="FEED_NOT_FOUND",
                    message="Feed not found",
                    details={"id": feed_id} if version_config.is_supported(api_version) else None
                ).dict()
            )
        
        cache_warmer = CacheWarmer(db)
        await cache_warmer.start_warming(background_tasks)
        
        return {
            "version": api_version,
            "message": "Cache warming started",
            "feed_id": feed_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error warming cache for feed {feed_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="CACHE_WARM_ERROR",
                message="Failed to warm cache",
                details={"id": feed_id} if version_config.is_supported(api_version) else None
            ).dict()
        )
    
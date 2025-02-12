from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.crud.article import article
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.models.user import User
from app.db.base import get_db
from app.core.deps import get_current_user
from app.core.versioning import version_config, APIVersion, VersionedResponse
from app.core.error_handler import ErrorDetail
from fastapi.responses import Response
from app.core.feed_generator import RSSFeedGenerator
from app.core.redis_cache import cache
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles")

class ArticleResponse(VersionedResponse):
    data: List[Article]
    total: int = 0
    page: int = 1
    page_size: int = 100

@router.get("", response_model=ArticleResponse)
async def read_articles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    cache_key = f"articles:{current_user.id}:{skip}:{limit}"
    cached_data = cache.get_cache(cache_key)
    if cached_data:
        return ArticleResponse(**cached_data)

    """
    Retrieve articles. This endpoint requires authentication.
    
    Version changes:
    - 1.0: Base implementation
    - 1.1: Added pagination metadata
    - 2.0: Added filtering and sorting
    """
    try:
        logger.info(f"Getting articles with skip={skip} and limit={limit}")
        
        # Version-specific logic
        if api_version >= APIVersion.V2:
            # V2: Include filtering and sorting
            articles = article.get_multi_filtered(db, skip=skip, limit=limit)
        else:
            # V1: Basic pagination
            articles = article.get_multi(db, skip=skip, limit=limit)
        
        total_count = len(articles)
        logger.info(f"Found {total_count} articles")
        
        return ArticleResponse(
            version=api_version,
            data=articles,
            total=total_count,
            page=(skip // limit) + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving articles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="ARTICLE_FETCH_ERROR",
                message="Error retrieving articles",
                details={"error": str(e)} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.post("", response_model=Article)
async def create_article(
    *,
    db: Session = Depends(get_db),
    article_in: ArticleCreate,
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Create new article. This endpoint requires authentication."""
    try:
        logger.info(f"Creating article with title: {article_in.title}")
        article_obj = article.create(db, obj_in=article_in)
        logger.info(f"Successfully created article with id: {article_obj.id}")
        return article_obj
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="ARTICLE_CREATE_ERROR",
                message=f"Error creating article: {str(e)}",
                details={"title": article_in.title} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.put("/{article_id}", response_model=Article)
async def update_article(
    *,
    db: Session = Depends(get_db),
    article_id: int,
    article_in: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Update article. This endpoint requires authentication."""
    try:
        article_obj = article.get(db, id=article_id)
        if not article_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="ARTICLE_NOT_FOUND",
                    message="Article not found",
                    details={"id": article_id} if version_config.is_supported(api_version) else None
                ).dict()
            )
        article_obj = article.update(db, db_obj=article_obj, obj_in=article_in)
        return article_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="ARTICLE_UPDATE_ERROR",
                message="Error updating article",
                details={"id": article_id} if version_config.is_supported(api_version) else None
            ).dict()
        )

@router.delete("/{article_id}")
async def delete_article(
    *,
    db: Session = Depends(get_db),
    article_id: int,
    current_user: User = Depends(get_current_user),
    api_version: str = Depends(version_config.verify_version)
):
    """Delete article. This endpoint requires authentication."""
    try:
        article_obj = article.get(db, id=article_id)
        if not article_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code="ARTICLE_NOT_FOUND",
                    message="Article not found",
                    details={"id": article_id} if version_config.is_supported(api_version) else None
                ).dict()
            )
        article.remove(db, id=article_id)
        return {"message": "Article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="ARTICLE_DELETE_ERROR",
                message="Error deleting article",
                details={"id": article_id} if version_config.is_supported(api_version) else None
            ).dict()
        )
    
@router.get("/feed.rss")
async def get_rss_feed(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Generate RSS feed of latest articles."""
    articles = article.get_multi(db, limit=limit)
    
    feed_gen = RSSFeedGenerator()
    feed_gen.add_articles(articles)
    
    return Response(
        content=feed_gen.get_rss(),
        media_type="application/rss+xml"
    )

@router.get("/feed.atom")
async def get_atom_feed(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Generate Atom feed of latest articles."""
    articles = article.get_multi(db, limit=limit)
    
    feed_gen = RSSFeedGenerator()
    feed_gen.add_articles(articles)
    
    return Response(
        content=feed_gen.get_atom(),
        media_type="application/atom+xml"
    )

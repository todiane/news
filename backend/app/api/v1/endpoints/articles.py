from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.crud.article import article
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.models.user import User
from app.db.base import get_db
from app.core.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles")

@router.get("", response_model=List[Article])
def read_articles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve articles. This endpoint requires authentication.
    """
    logger.info(f"Getting articles with skip={skip} and limit={limit}")
    articles = article.get_multi(db, skip=skip, limit=limit)
    logger.info(f"Found {len(articles)} articles")
    return articles

@router.post("", response_model=Article)
def create_article(
    *,
    db: Session = Depends(get_db),
    article_in: ArticleCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new article. This endpoint requires authentication.
    """
    logger.info(f"Creating article with title: {article_in.title}")
    try:
        article_obj = article.create(db, obj_in=article_in)
        logger.info(f"Successfully created article with id: {article_obj.id}")
        return article_obj
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating article: {str(e)}"
        )

@router.put("/{article_id}", response_model=Article)
def update_article(
    *,
    db: Session = Depends(get_db),
    article_id: int,
    article_in: ArticleUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update article. This endpoint requires authentication.
    """
    article_obj = article.get(db, id=article_id)
    if not article_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    article_obj = article.update(db, db_obj=article_obj, obj_in=article_in)
    return article_obj

@router.delete("/{article_id}")
def delete_article(
    *,
    db: Session = Depends(get_db),
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete article. This endpoint requires authentication.
    """
    article_obj = article.get(db, id=article_id)
    if not article_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    article.remove(db, id=article_id)
    return {"message": "Article deleted successfully"}
from typing import List, Optional
from sqlalchemy.orm import Session
from ..crud.base import CRUDBase
from ..models.article import Article
from ..schemas.article import ArticleCreate, ArticleUpdate

class CRUDArticle(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    def get_by_title(self, db: Session, *, title: str) -> Optional[Article]:
        return db.query(Article).filter(Article.title == title).first()
    
    def get_by_source(self, db: Session, *, source: str, skip: int = 0, limit: int = 100) -> List[Article]:
        return db.query(Article).filter(Article.source == source).offset(skip).limit(limit).all()

article = CRUDArticle(Article)
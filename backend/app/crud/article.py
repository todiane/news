from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..crud.base import CRUDBase
from ..models.article import Article
from ..schemas.article import ArticleCreate, ArticleUpdate

class CRUDArticle(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    def create(self, db: Session, *, obj_in: ArticleCreate) -> Article:
        db_obj = Article(
            title=obj_in.title,
            content=obj_in.content,
            url=str(obj_in.url),  # Convert Pydantic HttpUrl to string
            source=obj_in.source,
            published_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_title(self, db: Session, *, title: str) -> Optional[Article]:
        return db.query(Article).filter(Article.title == title).first()
    
    def get_by_source(self, db: Session, *, source: str, skip: int = 0, limit: int = 100) -> List[Article]:
        return db.query(Article).filter(Article.source == source).offset(skip).limit(limit).all()

article = CRUDArticle(Article)
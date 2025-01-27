# /backend/app/tests/crud_test.py
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.crud.article import CRUDArticle
from app.models.article import Article
from datetime import datetime

def test_crud_operations():
    db = SessionLocal()
    try:
        # Create
        article_data = {
            "title": "Test Article",
            "content": "This is a test article",
            "url": "https://test.com/article",
            "source": "Test Source",
            "published_date": datetime.utcnow()
        }
        
        article = Article(**article_data)
        db.add(article)
        db.commit()
        db.refresh(article)
        print("✅ Create Test: Article created successfully")

        # Read
        saved_article = db.query(Article).filter(Article.title == "Test Article").first()
        if saved_article:
            print("✅ Read Test: Article retrieved successfully")
            print(f"Title: {saved_article.title}")
            print(f"Content: {saved_article.content}")

        # Update
        saved_article.title = "Updated Test Article"
        db.commit()
        db.refresh(saved_article)
        print("✅ Update Test: Article updated successfully")

        # Delete
        db.delete(saved_article)
        db.commit()
        print("✅ Delete Test: Article deleted successfully")

    finally:
        db.close()

if __name__ == "__main__":
    test_crud_operations()
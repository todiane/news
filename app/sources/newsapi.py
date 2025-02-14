# /sources/newsapi.py
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from .base import NewsSourceBase
from ..models.article import Article
from ..core.config import settings

logger = logging.getLogger(__name__)

class NewsAPISource(NewsSourceBase):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.source_name = "newsapi"
        
    async def fetch_articles(self, query: str = "technology") -> List[Article]:
        """Fetch articles from NewsAPI"""
        headers = {"X-Api-Key": self.api_key}
        
        # Get articles from last 24 hours
        date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = (f"{self.base_url}/everything?"
               f"q={query}&"
               f"from={date_from}&"
               f"sortBy=publishedAt&"
               f"language=en")
               
        response = await self.handle_request(url, headers)
        
        if not response:
            return []
            
        return await self.process_response(response)
        
    async def validate_source(self) -> bool:
        """Validate NewsAPI configuration"""
        try:
            headers = {"X-Api-Key": self.api_key}
            response = await self.handle_request(f"{self.base_url}/sources", headers)
            return response is not None and response.get("status") == "ok"
        except Exception as e:
            logger.error(f"NewsAPI validation error: {e}")
            return False
            
    async def process_response(self, response: dict) -> List[Article]:
        """Process NewsAPI response into Article objects"""
        articles = []
        
        for item in response.get("articles", []):
            try:
                article = Article(
                    title=item.get("title", ""),
                    content=item.get("description", ""),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "NewsAPI"),
                    source_id=item.get("source", {}).get("id"),
                    api_source="newsapi",
                    category="technology",
                    author=item.get("author", ""),
                    published_date=self.normalize_date(item.get("publishedAt", "")),
                    extra_data={
                        "urlToImage": item.get("urlToImage"),
                        "content": item.get("content"),
                    }
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error processing NewsAPI article: {e}")
                
        return articles
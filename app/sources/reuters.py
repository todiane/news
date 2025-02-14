# /sources/reuters.py
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from .base import NewsSourceBase
from ..models.article import Article
from ..core.config import settings

logger = logging.getLogger(__name__)

class ReutersSource(NewsSourceBase):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "http://api.reuters.com/v2"
        self.source_name = "reuters"
        
    async def fetch_articles(self) -> List[Article]:
        """Fetch articles from Reuters API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        url = f"{self.base_url}/latest-news"
        response = await self.handle_request(url, headers)
        
        if not response:
            return []
            
        return await self.process_response(response)
        
    async def validate_source(self) -> bool:
        """Validate Reuters API configuration"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.handle_request(f"{self.base_url}/status", headers)
            return response is not None and response.get("status") == "ok"
        except Exception as e:
            logger.error(f"Reuters validation error: {e}")
            return False
            
    async def process_response(self, response: dict) -> List[Article]:
        """Process Reuters API response into Article objects"""
        articles = []
        
        for item in response.get("results", []):
            try:
                article = Article(
                    title=item.get("headline", ""),
                    content=item.get("body", ""),
                    url=item.get("url", ""),
                    source="Reuters",
                    source_id=item.get("id"),
                    api_source="reuters",
                    category=item.get("category", {}).get("label", ""),
                    author=item.get("authors", [{}])[0].get("name", ""),
                    published_date=self.normalize_date(item.get("datePublished", "")),
                    extra_data={
                        "tags": item.get("tags", []),
                        "channel": item.get("channel", ""),
                    }
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error processing Reuters article: {e}")
                
        return articles
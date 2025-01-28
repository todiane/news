import aiohttp
import feedparser
from datetime import datetime
from typing import List, Dict, Any
from .cache import cached
from ..schemas.article import ArticleCreate
from ..core.config import settings

class FeedFetcher:
    """
    Handles fetching and parsing of RSS feeds with caching support.
    """
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @cached(ttl=300)  # Cache RSS feeds for 5 minutes
    async def fetch_rss(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed, returning a list of standardized article entries.
        """
        try:
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries:
                    article = {
                        "title": entry.get("title", ""),
                        "content": entry.get("description", ""),
                        "url": entry.get("link", ""),
                        "source": feed.feed.get("title", "Unknown"),
                        "published_date": self._parse_date(entry.get("published", "")),
                        "author": entry.get("author", ""),
                        "category": entry.get("category", ""),
                        "extra_data": {
                            "guid": entry.get("id", ""),
                            "tags": [tag.term for tag in entry.get("tags", [])],
                            "comments_url": entry.get("comments", ""),
                        }
                    }
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            print(f"Error fetching RSS feed {feed_url}: {str(e)}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse various date formats into datetime object.
        Returns current UTC time if parsing fails.
        """
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                return datetime.utcnow()

async def fetch_all_feeds(feed_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch multiple RSS feeds concurrently and combine their articles.
    """
    all_articles = []
    
    async with FeedFetcher() as fetcher:
        for url in feed_urls:
            articles = await fetcher.fetch_rss(url)
            all_articles.extend(articles)
    
    # Sort by published date, newest first
    return sorted(all_articles, 
                 key=lambda x: x["published_date"], 
                 reverse=True)
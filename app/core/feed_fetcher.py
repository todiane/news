from typing import List, Dict, Any, Optional
import aiohttp
import feedparser
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedFetcher:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch and parse feed content."""
        try:
            if not self.session:
                async with aiohttp.ClientSession() as session:
                    return await self._fetch_with_session(session, url)
            return await self._fetch_with_session(self.session, url)
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {str(e)}")
            return None

    async def _fetch_with_session(self, session: aiohttp.ClientSession, url: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch feed content with provided session."""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                content = await response.text()
                feed = feedparser.parse(content)
                return self._parse_entries(feed)
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {str(e)}")
            return None

    def _parse_entries(self, feed) -> List[Dict[str, Any]]:
        """Parse feed entries into standardized format."""
        entries = []
        for entry in feed.entries:
            entries.append({
                'title': entry.get('title', ''),
                'content': entry.get('description', ''),
                'url': entry.get('link', ''),
                'published_date': self._parse_date(entry.get('published', '')),
                'author': entry.get('author', ''),
                'source': feed.feed.get('title', 'Unknown')
            })
        return entries

    def _parse_date(self, date_str: str) -> datetime:
        """Parse feed date string to datetime."""
        try:
            return datetime(*feedparser._parse_date(date_str)[:6])
        except:
            return datetime.utcnow()

feed_fetcher = FeedFetcher()

# /sources/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
import logging
from ..models.article import Article

logger = logging.getLogger(__name__)

class NewsSourceBase(ABC):
    """Base class for all news sources"""
    
    def __init__(self):
        self.session = None
        self.source_name = "base"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_articles(self) -> List[Article]:
        """Fetch articles from the source"""
        pass

    @abstractmethod
    async def validate_source(self) -> bool:
        """Validate the news source configuration"""
        pass

    async def process_response(self, response: Dict[str, Any]) -> List[Article]:
        """Process API response into Article objects"""
        pass

    def normalize_date(self, date_str: str) -> datetime:
        """Normalize different date formats to datetime"""
        try:
            # Add date parsing logic for your specific sources
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return datetime.utcnow()

    async def handle_request(self, url: str, headers: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                logger.error(f"Error fetching from {url}: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        
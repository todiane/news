from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Any
from fastapi import BackgroundTasks
from .cache import CacheManager
from .feed_fetcher import FeedFetcher
from app.crud.feed import feed as feed_crud
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class CacheWarmer:
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
        self.feed_fetcher = FeedFetcher()
        self.warming_interval = 300  # 5 minutes
        self.access_threshold = 10   # Number of accesses to consider a feed "popular"
        self._access_counts: Dict[str, int] = {}
        self._last_accessed: Dict[str, datetime] = {}

    async def start_warming(self, background_tasks: BackgroundTasks):
        """Start the cache warming process in the background."""
        background_tasks.add_task(self._warm_cache_periodically)

    async def _warm_cache_periodically(self):
        """Periodically warm the cache for frequently accessed feeds."""
        while True:
            try:
                popular_feeds = self._get_popular_feeds()
                for feed_url in popular_feeds:
                    await self._warm_single_feed(feed_url)
                
                # Clean up old access counts
                self._cleanup_access_counts()
                
                # Log warming metrics
                logger.info(f"Cache warmed for {len(popular_feeds)} popular feeds")
                
                await asyncio.sleep(self.warming_interval)
            except Exception as e:
                logger.error(f"Error during cache warming: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    def record_access(self, feed_url: str):
        """Record an access to a feed for popularity tracking."""
        current_time = datetime.utcnow()
        self._access_counts[feed_url] = self._access_counts.get(feed_url, 0) + 1
        self._last_accessed[feed_url] = current_time

    async def _warm_single_feed(self, feed_url: str):
        """Warm the cache for a single feed."""
        try:
            async with self.feed_fetcher as fetcher:
                articles = await fetcher.fetch_rss(feed_url)
                
                # Store in cache with a longer TTL for warmed items
                self.cache_manager.set(
                    f"warm_feed_{feed_url}",
                    articles,
                    ttl=self.warming_interval * 2
                )
                
                logger.info(f"Warmed cache for feed: {feed_url}")
                return True
        except Exception as e:
            logger.error(f"Error warming cache for {feed_url}: {str(e)}")
            return False

    def _get_popular_feeds(self) -> List[str]:
        """Get list of frequently accessed feeds."""
        current_time = datetime.utcnow()
        threshold_time = current_time - timedelta(minutes=30)
        
        return [
            feed_url
            for feed_url, last_access in self._last_accessed.items()
            if (last_access >= threshold_time and 
                self._access_counts.get(feed_url, 0) >= self.access_threshold)
        ]

    def _cleanup_access_counts(self):
        """Clean up old access counts."""
        current_time = datetime.utcnow()
        threshold_time = current_time - timedelta(hours=1)
        
        old_feeds = [
            feed_url
            for feed_url, last_access in self._last_accessed.items()
            if last_access < threshold_time
        ]
        
        for feed_url in old_feeds:
            self._access_counts.pop(feed_url, None)
            self._last_accessed.pop(feed_url, None)

    async def force_invalidate(self, feed_url: str):
        """Force invalidate a feed's cache."""
        cache_key = f"warm_feed_{feed_url}"
        self.cache_manager.invalidate(cache_key)
        logger.info(f"Forced cache invalidation for feed: {feed_url}")
        
        # Optionally, immediately rewarm the cache
        return await self._warm_single_feed(feed_url)

    def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        return {
            'total_feeds_tracked': len(self._access_counts),
            'popular_feeds_count': len(self._get_popular_feeds()),
            'access_counts': self._access_counts.copy(),
            'last_accessed': {
                url: time.isoformat() 
                for url, time in self._last_accessed.items()
            }
        }
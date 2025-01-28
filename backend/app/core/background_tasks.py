# app/core/background_tasks.py

from fastapi import BackgroundTasks
from datetime import datetime, timedelta
import asyncio
import logging
from typing import List
from sqlalchemy.orm import Session
from app.crud.feed import feed as feed_crud
from app.core.feed_fetcher import FeedFetcher
from app.core.cache import CacheManager

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self.feed_fetcher = FeedFetcher()
        self.cache = CacheManager()
        self.running = False
        self.refresh_interval = 300  # 5 minutes

    async def start_feed_refresh_task(self, background_tasks: BackgroundTasks):
        """Start the feed refresh background task."""
        if not self.running:
            background_tasks.add_task(self._refresh_feeds_periodically)
            self.running = True

    async def _refresh_feeds_periodically(self):
        """Periodically refresh all active feeds."""
        while True:
            try:
                feeds = await self._get_feeds_to_refresh()
                for feed in feeds:
                    try:
                        await self.feed_fetcher.fetch_feed_with_cache(feed.url)
                        await self._update_feed_last_fetched(feed)
                    except Exception as e:
                        logger.error(f"Error refreshing feed {feed.url}: {str(e)}")
                    await asyncio.sleep(1)  # Prevent overwhelming sources
                
                await asyncio.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"Error in feed refresh task: {str(e)}")
                await asyncio.sleep(60)

    async def _get_feeds_to_refresh(self) -> List:
        """Get feeds that need refreshing."""
        threshold = datetime.utcnow() - timedelta(seconds=self.refresh_interval)
        return feed_crud.get_feeds_to_refresh(threshold)

    async def _update_feed_last_fetched(self, feed):
        """Update the last_fetched timestamp for a feed."""
        feed.last_fetched = datetime.utcnow()
        await feed_crud.update(feed)

background_task_manager = BackgroundTaskManager()

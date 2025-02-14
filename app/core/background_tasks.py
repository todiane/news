from fastapi import BackgroundTasks
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Set
from app.db.base import get_db 
from app.core.feed_fetcher import feed_fetcher
from app.core.redis_cache import cache
from app.models.feed import Feed

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self.feed_fetcher = feed_fetcher
        self.cache = cache
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
        self.refresh_interval = 300
        self.stopping = False

    async def start(self, background_tasks: BackgroundTasks):
        if not self.running:
            logger.info("Starting background tasks...")
            self.stopping = False
            self.running = True
            feed_task = asyncio.create_task(self._refresh_feeds_periodically())
            self.tasks.add(feed_task)
            feed_task.add_done_callback(self.tasks.discard)
            logger.info("Background tasks started successfully")

    async def stop(self):
        logger.info("Stopping background tasks...")
        self.stopping = True
        self.running = False
        for task in self.tasks:
            if not task.done():
                task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        logger.info("Background tasks stopped successfully")

    async def _refresh_feeds_periodically(self):
        while not self.stopping:
            try:
                db = next(get_db())
                threshold = datetime.utcnow() - timedelta(minutes=5)
                feeds = db.query(Feed).filter(Feed.last_fetched <= threshold).all()
                
                for feed in feeds:
                    if self.stopping:
                        break
                    try:
                        await self._process_feed_updates(feed)
                    except Exception as e:
                        logger.error(f"Error processing feed {feed.id}: {str(e)}")
                    await asyncio.sleep(1)
                
                db.close()
                await asyncio.sleep(self.refresh_interval)
            except asyncio.CancelledError:
                logger.info("Feed refresh task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in feed refresh task: {str(e)}")
                await asyncio.sleep(60)

    async def _process_feed_updates(self, feed: Feed):
        try:
            cache_key = f"feed_content:{feed.id}"
            cached_content = self.cache.get_cache(cache_key)
            if cached_content:
                return cached_content

            new_content = await self.feed_fetcher.fetch(feed.url)
            if new_content:
                self.cache.set_cache(cache_key, new_content)
                db = next(get_db())
                feed.last_fetched = datetime.utcnow()
                db.commit()
                db.close()
        except Exception as e:
            logger.error(f"Error processing feed {feed.id} updates: {str(e)}")

background_task_manager = BackgroundTaskManager()

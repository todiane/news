# app/core/background_tasks.py

from fastapi import BackgroundTasks
from datetime import datetime, timedelta
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from app.crud.feed import feed as feed_crud
from app.crud.user import user as user_crud
from app.core.feed_fetcher import FeedFetcher
from app.core.cache import CacheManager
from app.core.notification_manager import notification_manager
from app.models.feed_preference import FeedPreference
from app.models.feed import Feed
from app.models.user import User

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self.feed_fetcher = FeedFetcher()
        self.cache = CacheManager()
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
        
        # Intervals
        self.refresh_interval = 300  # 5 minutes
        self.notification_check_interval = 60  # 1 minute
        
        # Notification batches
        self.notification_batches: Dict[str, List[Dict[str, Any]]] = {
            'hourly': [],
            'daily': [],
            'weekly': []
        }
        
        # Task state
        self.stopping = False

    async def start(self, background_tasks: BackgroundTasks):
        """Start all background tasks."""
        if not self.running:
            logger.info("Starting background tasks...")
            self.stopping = False
            self.running = True
            
            # Create and store task references
            feed_task = asyncio.create_task(self._refresh_feeds_periodically())
            notification_task = asyncio.create_task(self._process_notifications_periodically())
            
            self.tasks.add(feed_task)
            self.tasks.add(notification_task)
            
            feed_task.add_done_callback(self.tasks.discard)
            notification_task.add_done_callback(self.tasks.discard)
            
            logger.info("Background tasks started successfully")

    async def stop(self):
        """Gracefully stop all background tasks."""
        logger.info("Stopping background tasks...")
        self.stopping = True
        self.running = False
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
        logger.info("Background tasks stopped successfully")

    async def _refresh_feeds_periodically(self):
        """Periodically refresh all active feeds and handle notifications."""
        while not self.stopping:
            try:
                feeds = await self._get_feeds_to_refresh()
                for feed in feeds:
                    if self.stopping:
                        break
                        
                    try:
                        # Fetch and process new content
                        await self._process_feed_updates(feed)
                    except Exception as e:
                        logger.error(f"Error processing feed {feed.id}: {str(e)}")
                    
                    # Prevent overwhelming sources
                    await asyncio.sleep(1)
                
                await asyncio.sleep(self.refresh_interval)
            except asyncio.CancelledError:
                logger.info("Feed refresh task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in feed refresh task: {str(e)}")
                await asyncio.sleep(60)

    async def _get_feeds_to_refresh(self) -> List[Feed]:
        """Get feeds that need refreshing."""
        try:
            threshold = datetime.utcnow() - timedelta(seconds=self.refresh_interval)
            return await feed_crud.get_feeds_to_refresh(threshold)
        except Exception as e:
            logger.error(f"Error getting feeds to refresh: {str(e)}")
            return []

    async def _process_feed_updates(self, feed: Feed):
        """Process updates for a single feed."""
        try:
            # Fetch new content
            new_content = await self.feed_fetcher.fetch_feed_with_cache(feed.url)
            if not new_content:
                return

            # Get cached content
            cache_key = f"feed_{feed.id}_content"
            cached_content = self.cache.get(cache_key)

            # Find new updates
            new_updates = self._find_new_updates(new_content, cached_content)
            if new_updates:
                # Process notifications
                await self._handle_new_updates(feed, new_updates)
                
                # Update cache with new content
                self.cache.set(cache_key, new_content)

            # Update feed metadata
            await self._update_feed_metadata(feed)

        except Exception as e:
            logger.error(f"Error processing feed {feed.id} updates: {str(e)}")

    async def _process_notifications_periodically(self):
        """Periodically process and send batched notifications."""
        while not self.stopping:
            try:
                current_time = datetime.utcnow()
                
                # Process each notification frequency
                for frequency in ['hourly', 'daily', 'weekly']:
                    await self._process_frequency_notifications(frequency, current_time)
                
                # Clean up old notifications
                self._clear_old_notifications()
                
                await asyncio.sleep(self.notification_check_interval)
            except asyncio.CancelledError:
                logger.info("Notification processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing notifications: {str(e)}")
                await asyncio.sleep(60)

    async def _process_frequency_notifications(self, frequency: str, current_time: datetime):
        """Process notifications for a specific frequency."""
        try:
            preferences = await feed_crud.get_preferences_by_frequency(frequency)
            for pref in preferences:
                if self._should_send_notification(pref, frequency, current_time):
                    batch = self.notification_batches[frequency]
                    if batch:
                        # Get relevant updates for this feed
                        feed_updates = [
                            update for update in batch 
                            if update.get('feed_id') == pref.feed_id
                        ]
                        
                        if feed_updates:
                            await notification_manager.notify_feed_updates(
                                pref.user,
                                pref.feed_id,
                                feed_updates
                            )
                            
                            # Remove sent updates from batch
                            self.notification_batches[frequency] = [
                                update for update in batch 
                                if update not in feed_updates
                            ]
                            
                            # Update last notification time
                            await feed_crud.update_last_notification(pref.id, current_time)
        except Exception as e:
            logger.error(f"Error processing {frequency} notifications: {str(e)}")

    def _find_new_updates(self, new_content: List[dict], cached_content: Optional[List[dict]]) -> List[dict]:
        """Compare new content with cached content to find updates."""
        if not cached_content:
            return new_content
        
        cached_urls = {item.get('url') for item in cached_content}
        return [item for item in new_content if item.get('url') not in cached_urls]

    async def _update_feed_metadata(self, feed: Feed):
        """Update feed metadata after refresh."""
        try:
            feed.last_fetched = datetime.utcnow()
            feed.last_updated = datetime.utcnow()
            await feed_crud.update(feed)
        except Exception as e:
            logger.error(f"Error updating feed metadata: {str(e)}")

    def _should_send_notification(self, pref: FeedPreference, frequency: str, current_time: datetime) -> bool:
        """Determine if notification should be sent based on frequency and last notification time."""
        if not pref.last_notification_sent:
            return True

        time_diff = current_time - pref.last_notification_sent
        
        if frequency == 'hourly':
            return time_diff >= timedelta(hours=1)
        elif frequency == 'daily':
            return time_diff >= timedelta(days=1)
        elif frequency == 'weekly':
            return time_diff >= timedelta(weeks=1)
            
        return False

    def _clear_old_notifications(self):
        """Remove old notifications from batches."""
        try:
            max_age = timedelta(days=7)  # Keep notifications for up to a week
            current_time = datetime.utcnow()
            
            for frequency in self.notification_batches:
                self.notification_batches[frequency] = [
                    update for update in self.notification_batches[frequency]
                    if current_time - update.get('timestamp', current_time) < max_age
                ]
        except Exception as e:
            logger.error(f"Error clearing old notifications: {str(e)}")

    def add_to_notification_batch(self, updates: List[Dict[str, Any]], frequency: str):
        """Add updates to the appropriate notification batch."""
        if frequency in self.notification_batches:
            timestamp = datetime.utcnow()
            for update in updates:
                update['timestamp'] = timestamp
            self.notification_batches[frequency].extend(updates)

background_task_manager = BackgroundTaskManager()

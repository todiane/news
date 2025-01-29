# backend/app/services/feed_validator.py

import aiohttp
import feedparser
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import re
from datetime import datetime

class FeedValidationError(Exception):
    """Custom exception for feed validation errors"""
    pass

class FeedValidator:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def validate_feed(self, url: str, feed_type: str = 'rss') -> Tuple[bool, Optional[str]]:
        """
        Validate a feed URL and return whether it's valid and any error message.
        
        Args:
            url: The URL to validate
            feed_type: Type of feed ('rss' or 'youtube')
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Basic URL validation
        if not self._is_valid_url(url):
            return False, "Invalid URL format"

        try:
            if feed_type == 'youtube':
                return await self._validate_youtube_feed(url)
            else:
                return await self._validate_rss_feed(url)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    async def _validate_rss_feed(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate an RSS/Atom feed."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False, f"HTTP error: {response.status}"

                content = await response.text()
                feed = feedparser.parse(content)

                # Check if it's a valid feed
                if feed.bozo:
                    return False, f"Invalid feed format: {feed.bozo_exception}"

                # Check for required feed elements
                if not hasattr(feed, 'feed') or not hasattr(feed, 'entries'):
                    return False, "Missing required feed elements"

                # Check for recent entries
                if not feed.entries:
                    return False, "Feed contains no entries"

                # Validate feed structure
                validation_result = self._validate_feed_structure(feed)
                if not validation_result[0]:
                    return validation_result

                return True, None

        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def _validate_youtube_feed(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate a YouTube feed URL."""
        # Extract channel ID or username from URL
        channel_id = self._extract_youtube_channel_id(url)
        if not channel_id:
            return False, "Invalid YouTube URL format"

        # Construct feed URL
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        try:
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    return False, "Invalid YouTube channel"

                content = await response.text()
                feed = feedparser.parse(content)

                if not feed.entries:
                    return False, "No videos found in channel feed"

                return True, None

        except Exception as e:
            return False, f"YouTube feed validation error: {str(e)}"

    def _extract_youtube_channel_id(self, url: str) -> Optional[str]:
        """Extract YouTube channel ID from various URL formats."""
        patterns = [
            r'youtube\.com/channel/(UC[\w-]+)',  # Channel ID format
            r'youtube\.com/user/([\w-]+)',       # Username format
            r'youtube\.com/@([\w-]+)',           # Handle format
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _validate_feed_structure(self, feed) -> Tuple[bool, Optional[str]]:
        """Validate the structure of a parsed feed."""
        required_feed_fields = ['title', 'link']
        required_entry_fields = ['title', 'link', 'published']

        # Check feed fields
        for field in required_feed_fields:
            if not hasattr(feed.feed, field):
                return False, f"Feed missing required field: {field}"

        # Check at least one entry
        if not feed.entries:
            return False, "Feed contains no entries"

        # Check first entry fields
        first_entry = feed.entries[0]
        for field in required_entry_fields:
            if not hasattr(first_entry, field):
                return False, f"Feed entries missing required field: {field}"

        # Check if feed is too old
        try:
            latest_entry_date = datetime(*first_entry.published_parsed[:6])
            if (datetime.now() - latest_entry_date).days > 365:
                return False, "Feed appears to be inactive (no updates in over a year)"
        except:
            pass  # Skip date validation if parsing fails

        return True, None
    
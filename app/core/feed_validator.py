# app/core/feed_validator.py
import aiohttp
import feedparser
from typing import Dict, Optional, Tuple
import re
from urllib.parse import urlparse
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FeedValidator:
    """Validates and analyzes RSS/Atom feeds."""
    
    def __init__(self):
        self.session = None
        self.common_feed_paths = [
            '/feed',
            '/rss',
            '/atom',
            '/feed.xml',
            '/rss.xml',
            '/atom.xml',
            '/feed/rss',
            '/feed/atom',
            '/rss/feed',
            '/index.xml'
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def validate_feed(self, url: str) -> Tuple[bool, Dict]:
        """
        Validates a feed URL and returns validation status and details.
        
        Args:
            url: The URL to validate
            
        Returns:
            Tuple containing:
                - Boolean indicating if feed is valid
                - Dict with validation details and feed metadata
        """
        try:
            # Basic URL validation
            if not self._is_valid_url(url):
                return False, {
                    "error": "Invalid URL format",
                    "details": "The provided URL is not properly formatted"
                }

            # Fetch and validate feed content
            feed_content = await self._fetch_feed(url)
            if not feed_content:
                return False, {
                    "error": "Failed to fetch feed",
                    "details": "Could not retrieve content from the provided URL"
                }

            # Parse and validate feed structure
            feed = feedparser.parse(feed_content)
            validation_result = self._validate_feed_structure(feed)
            
            if not validation_result["is_valid"]:
                return False, validation_result

            # Extract and validate feed metadata
            metadata = self._extract_feed_metadata(feed)
            
            return True, {
                "is_valid": True,
                "metadata": metadata,
                "format": self._detect_feed_format(feed),
                "stats": self._calculate_feed_stats(feed)
            }

        except Exception as e:
            logger.error(f"Error validating feed {url}: {str(e)}")
            return False, {
                "error": "Validation error",
                "details": str(e)
            }

    def _is_valid_url(self, url: str) -> bool:
        """Validates URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    async def _fetch_feed(self, url: str) -> Optional[str]:
        """Fetches feed content from URL."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            logger.error(f"Error fetching feed: {str(e)}")
            return None

    def _validate_feed_structure(self, feed) -> Dict:
        """Validates the basic structure of the feed."""
        if feed.bozo:
            return {
                "is_valid": False,
                "error": "Invalid feed format",
                "details": str(feed.bozo_exception) if feed.bozo_exception else "Unknown parsing error"
            }

        if not hasattr(feed, 'feed') or not hasattr(feed, 'entries'):
            return {
                "is_valid": False,
                "error": "Invalid feed structure",
                "details": "Feed is missing required elements"
            }

        if not feed.entries:
            return {
                "is_valid": False,
                "error": "Empty feed",
                "details": "Feed contains no entries"
            }

        return {"is_valid": True}

    def _extract_feed_metadata(self, feed) -> Dict:
        """Extracts metadata from the feed."""
        return {
            "title": feed.feed.get("title", ""),
            "description": feed.feed.get("description", ""),
            "language": feed.feed.get("language", ""),
            "last_updated": self._parse_date(feed.feed.get("updated", "")),
            "author": feed.feed.get("author", ""),
            "generator": feed.feed.get("generator", ""),
            "links": [link.get("href", "") for link in feed.feed.get("links", [])],
            "image": feed.feed.get("image", {}).get("href", "") if "image" in feed.feed else ""
        }

    def _detect_feed_format(self, feed) -> str:
        """Detects the feed format (RSS or Atom)."""
        if feed.version.startswith('atom'):
            return 'atom'
        elif feed.version.startswith('rss'):
            return 'rss'
        return 'unknown'

    def _calculate_feed_stats(self, feed) -> Dict:
        """Calculates basic statistics about the feed."""
        return {
            "total_entries": len(feed.entries),
            "average_entry_length": self._calculate_average_entry_length(feed.entries),
            "has_images": any(
                "media_content" in entry or "enclosures" in entry 
                for entry in feed.entries
            ),
            "update_frequency": self._estimate_update_frequency(feed.entries)
        }

    def _calculate_average_entry_length(self, entries) -> int:
        """Calculates average entry length in characters."""
        if not entries:
            return 0
        total_length = sum(
            len(entry.get("description", "")) + len(entry.get("title", ""))
            for entry in entries
        )
        return total_length // len(entries)

    def _estimate_update_frequency(self, entries) -> Optional[float]:
        """Estimates the average time between posts in hours."""
        if len(entries) < 2:
            return None

        dates = []
        for entry in entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                dates.append(datetime(*published[:6], tzinfo=timezone.utc))

        if len(dates) < 2:
            return None

        dates.sort(reverse=True)
        time_diffs = [
            (dates[i] - dates[i+1]).total_seconds() / 3600
            for i in range(len(dates)-1)
        ]
        
        return sum(time_diffs) / len(time_diffs)

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parses date string into ISO format."""
        if not date_str:
            return None
        try:
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6]).isoformat()
            return None
        except:
            return None

    async def discover_feed_url(self, website_url: str) -> Optional[str]:
        """
        Attempts to discover RSS/Atom feed URL from a website URL.
        
        Args:
            website_url: The website URL to check for feeds
            
        Returns:
            Discovered feed URL or None if not found
        """
        try:
            # Try common feed paths first
            for path in self.common_feed_paths:
                parsed = urlparse(website_url)
                feed_url = f"{parsed.scheme}://{parsed.netloc}{path}"
                
                async with self.session.get(feed_url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'xml' in content_type or 'rss' in content_type or 'atom' in content_type:
                            return feed_url

            # If no common paths work, try to parse the HTML for feed links
            async with self.session.get(website_url) as response:
                if response.status == 200:
                    html = await response.text()
                    feed_urls = re.findall(r'href=[\'"]?([^\'" >]+)[\'"]? type=["\'](application/rss\+xml|application/atom\+xml)["\']', html)
                    
                    if feed_urls:
                        feed_url = feed_urls[0][0]
                        if not feed_url.startswith(('http://', 'https://')):
                            parsed = urlparse(website_url)
                            feed_url = f"{parsed.scheme}://{parsed.netloc}{feed_url}"
                        return feed_url

            return None
            
        except Exception as e:
            logger.error(f"Error discovering feed URL for {website_url}: {str(e)}")
            return None

feed_validator = FeedValidator()

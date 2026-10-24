# feeds/services/feed_fetcher.py

import socket
import feedparser
import logging
from datetime import datetime
from django.utils import timezone
from calendar import timegm
from urllib.parse import urlparse, parse_qs
from ..models import RSSFeed, Content
from datetime import timezone as dt_timezone

FETCH_TIMEOUT = 20  # seconds; stops one slow feed hanging the whole run
ENTRIES_PER_FEED = 10

logger = logging.getLogger(__name__)

class FeedFetcher:
    def __init__(self):
        self.default_img = '/static/img/default_thumbnail.png'

    def fetch_feed(self, feed):
        """Fetch and process a single feed"""
        try:
            socket.setdefaulttimeout(FETCH_TIMEOUT)
            parsed_feed = feedparser.parse(feed.url, agent='DjangifyNews/2.0 (+https://news.djangify.com)')
            
            if hasattr(parsed_feed, 'bozo_exception') and parsed_feed.bozo_exception and not parsed_feed.entries:
                logger.error(f"Feed error for {feed.name}: {parsed_feed.bozo_exception}")
                feed.error_count += 1
                feed.save()
                return
            
            # Process entries if we have any, even if there was a bozo exception
            if not parsed_feed.entries:
                logger.error(f"No entries found in feed: {feed.name}")
                feed.error_count += 1
                feed.save()
                return
                
            for entry in parsed_feed.entries[:ENTRIES_PER_FEED]:
                try:
                    # Skip if content already exists
                    if Content.objects.filter(url=entry.link).exists():
                        continue

                    image_url = None
                    if feed.feed_type == 'youtube':
                        video_id = self.get_youtube_video_id(entry.link)
                        image_url = self.get_youtube_thumbnail(video_id)
                    else:
                        # Try to find image in entry
                        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                            image_url = entry.media_thumbnail[0]['url']
                        elif hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0]['url']
                    
                    # Try to extract an image from enclosures if available
                    if not image_url and hasattr(entry, 'enclosures'):
                        for enclosure in entry.enclosures:
                            if enclosure.get('type', '').startswith('image/'):
                                image_url = enclosure.get('href')
                                break
                    
                    # Use the feed's category directly
                    category = feed.category

                    # Get description from either summary or content
                    description = ''
                    if hasattr(entry, 'summary'):
                        description = entry.summary
                    elif hasattr(entry, 'content') and entry.content:
                        description = entry.content[0].value
                    
                    # Clean description - remove problematic characters if needed
                    description = self.clean_text(description)
                    
                    # Truncate image_url if too long (MySQL has a limit)
                    if image_url and len(image_url) > 1990:
                        image_url = image_url[:1990]
                    
                    # Get published date
                    published_date = self.entry_date(entry)

                    Content.objects.create(
                        title=self.clean_text(entry.title),
                        description=description,
                        url=entry.link,
                        image_url=image_url or self.default_img,
                        source=feed,
                        category=category,
                        published_date=published_date
                    )
                except Exception as e:
                    # Log the error but continue processing other entries
                    logger.error(f"Error processing entry {entry.get('title', 'Unknown')}: {str(e)}")
                    continue

            feed.last_fetched = timezone.now()
            feed.error_count = 0
            feed.save()

        except Exception as e:
            logger.error(f"Error fetching feed {feed.name}: {str(e)}")
            feed.error_count += 1
            feed.save()

    def clean_text(self, text):
        """Clean text to remove problematic characters."""
        if not text:
            return ""
        # Replace emojis and other problematic characters if needed
        return text.encode('utf-8', errors='ignore').decode('utf-8')


    def entry_date(self, entry):
        """Use feedparser's pre-parsed UTC time, else fall back to the string, else now"""
        parsed = entry.get('published_parsed') or entry.get('updated_parsed')
        if parsed:
            return datetime.fromtimestamp(timegm(parsed), tz=dt_timezone.utc)
        return self.parse_date(entry.get('published') or entry.get('updated'))

    def parse_date(self, date_string):
        """Parse a date string into a datetime object"""
        if not date_string:
            return timezone.now()
            
        try:
            # Try to parse as ISO format
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Use Python's dateutil parser as an alternative
                from dateutil import parser
                dt = parser.parse(date_string)
            except:
                # If all parsing fails, use current time
                return timezone.now()
            
        # Check if timezone info is missing and add UTC if it is
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_timezone.utc)
            
        return dt if dt else timezone.now()

    
    def get_youtube_video_id(self, url):
        """Extract video ID from YouTube URL"""
        parsed_url = urlparse(url)
        if parsed_url.netloc in ['www.youtube.com', 'youtube.com']:
            query = parse_qs(parsed_url.query)
            return query.get('v', [''])[0]
        elif parsed_url.netloc in ['youtu.be']:
            return parsed_url.path.lstrip('/')
        return ''
    
    def get_youtube_thumbnail(self, video_id):
        """Get thumbnail URL for YouTube video"""
        if not video_id:
            return None
        return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
# app/sources/rss.py
from datetime import datetime
from typing import List, Optional
import feedparser
import json
from app.models.article import Article

import logging
logger = logging.getLogger(__name__)

class RSSFeedSource:
    def __init__(self):
        self.tech_feeds = {
            "django": {
                "url": "https://www.djangoproject.com/rss/weblog/",
                "type": "blog"
            },
            "tailwind": {
                "url": "https://tailwindcss.com/feeds/feed.xml",
                "type": "blog"
            },
            "anthropic": {
                "url": "https://www.anthropic.com/feed",
                "type": "blog"
            },
            "fastapi": {
                "url": "https://fastapi.tiangolo.com/rss.xml",
                "type": "blog"
            },
        }
        
        self.video_feeds = {
            "youtube": {
                "django": "https://www.youtube.com/feeds/videos.xml?channel_id=UC8butISFwT-Wl7EV0hUK0BQ",  # Example: FreeCodeCamp
                "ai": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw",      # Example: Two Minute Papers
            }
        }

    async def fetch_articles(self, source_name: str) -> List[Article]:
        """Fetch articles from RSS feed"""
        try:
            feed_info = self.tech_feeds.get(source_name)
            if not feed_info:
                logger.error(f"Unknown RSS source: {source_name}")
                return []

            feed = feedparser.parse(feed_info["url"])
            if feed.bozo:
                logger.error(f"Invalid RSS feed for {source_name}: {feed.bozo_exception}")
                return []

            articles = []
            for entry in feed.entries:
                try:
                    # Handle different feed formats
                    content = entry.get('content', [{}])[0].get('value', '')
                    if not content:
                        content = entry.get('summary', '')

                    article = Article(
                        title=entry.get('title', ''),
                        content=content,
                        url=entry.get('link', ''),
                        source=source_name,
                        source_id=entry.get('id', ''),
                        api_source='rss',
                        category=feed_info["type"],
                        author=entry.get('author', ''),
                        published_date=self._parse_date(entry.get('published', '')),
                        metadata=json.dumps({
                            'tags': entry.get('tags', []),
                            'media': self._extract_media(entry)
                        })
                    )
                    articles.append(article)
                except Exception as e:
                    logger.error(f"Error processing RSS article: {e}")
                    continue

            return articles
        except Exception as e:
            logger.error(f"Error fetching RSS feed {source_name}: {e}")
            return []

    async def fetch_videos(self, channel: str) -> List[Article]:
        feed_url = self.video_feeds["youtube"].get(channel)
        if not feed_url:
            return []

        feed = feedparser.parse(feed_url)
        videos = []

        for entry in feed.entries:
            # Extract video ID from URL
            video_id = entry.get('yt_videoid', '')
            
            video = Article(
                title=entry.get('title', ''),
                content=entry.get('summary', ''),
                url=f"https://www.youtube.com/watch?v={video_id}",
                source=f"youtube_{channel}",
                source_id=video_id,
                api_source='youtube',
                category='video',
                author=entry.get('author', ''),
                published_date=self._parse_date(entry.get('published', '')),
                metadata=json.dumps({
                    'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    'duration': entry.get('media_duration', ''),
                    'views': entry.get('media_statistics', {}).get('views', 0)
                })
            )
            videos.append(video)

        return videos
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            return datetime.utcnow()

    def _extract_media(self, entry) -> dict:
        media = {}
        if 'media_content' in entry:
            media['content'] = entry.media_content
        if 'media_thumbnail' in entry:
            media['thumbnail'] = entry.media_thumbnail
        return media
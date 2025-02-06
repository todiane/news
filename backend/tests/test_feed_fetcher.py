import pytest
from unittest.mock import Mock, patch
import aiohttp
import feedparser
from datetime import datetime, timezone
from app.core.feed_fetcher import FeedFetcher
from app.core.cache import CacheManager

# Mock RSS feed data
MOCK_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <link>http://example.com</link>
        <description>Test RSS Feed</description>
        <item>
            <title>Test Article</title>
            <link>http://example.com/article1</link>
            <description>Test article content</description>
            <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
            <author>Test Author</author>
            <category>Technology</category>
        </item>
    </channel>
</rss>
"""

@pytest.fixture
async def feed_fetcher():
    async with FeedFetcher() as fetcher:
        yield fetcher

@pytest.fixture
def mock_cache():
    return Mock(spec=CacheManager)

@pytest.mark.asyncio
async def test_fetch_rss_success(feed_fetcher, mock_cache):
    """Test successful RSS feed fetching and parsing."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = Mock(return_value=MOCK_RSS_FEED)
        mock_get.return_value.__aenter__.return_value = mock_response

        articles = await feed_fetcher.fetch_rss("http://example.com/feed")
        
        assert len(articles) == 1
        article = articles[0]
        assert article["title"] == "Test Article"
        assert article["content"] == "Test article content"
        assert article["url"] == "http://example.com/article1"
        assert article["source"] == "Test Feed"
        assert article["author"] == "Test Author"
        assert article["category"] == "Technology"

@pytest.mark.asyncio
async def test_fetch_rss_invalid_url(feed_fetcher):
    """Test handling of invalid feed URLs."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = aiohttp.ClientError()
        
        articles = await feed_fetcher.fetch_rss("http://invalid-url.com/feed")
        assert articles == []

@pytest.mark.asyncio
async def test_fetch_rss_invalid_feed(feed_fetcher):
    """Test handling of invalid feed content."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = Mock(return_value="Invalid feed content")
        mock_get.return_value.__aenter__.return_value = mock_response

        articles = await feed_fetcher.fetch_rss("http://example.com/feed")
        assert articles == []

@pytest.mark.asyncio
async def test_fetch_rss_http_error(feed_fetcher):
    """Test handling of HTTP errors."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = Mock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        articles = await feed_fetcher.fetch_rss("http://example.com/feed")
        assert articles == []

@pytest.mark.asyncio
async def test_fetch_rss_with_cache(feed_fetcher, mock_cache):
    """Test feed fetching with caching."""
    cached_articles = [{"title": "Cached Article"}]
    mock_cache.get.return_value = cached_articles

    with patch('app.core.feed_fetcher.CacheManager', return_value=mock_cache):
        articles = await feed_fetcher.fetch_rss("http://example.com/feed")
        assert articles == cached_articles
        mock_cache.get.assert_called_once()

@pytest.mark.asyncio
async def test_parse_date_formats(feed_fetcher):
    """Test parsing of different date formats."""
    test_dates = [
        "Mon, 01 Jan 2024 12:00:00 GMT",
        "2024-01-01T12:00:00Z",
        "invalid date format"
    ]
    
    for date_str in test_dates:
        result = feed_fetcher._parse_date(date_str)
        assert isinstance(result, datetime)
        if date_str != "invalid date format":
            assert result.tzinfo == timezone.utc

@pytest.mark.asyncio
async def test_extract_media(feed_fetcher):
    """Test extraction of media content from feed entries."""
    entry = Mock()
    entry.media_content = [{"url": "http://example.com/image.jpg"}]
    entry.media_thumbnail = [{"url": "http://example.com/thumbnail.jpg"}]

    media = feed_fetcher._extract_media(entry)
    assert "content" in media
    assert "thumbnail" in media
    assert media["content"] == entry.media_content
    assert media["thumbnail"] == entry.media_thumbnail
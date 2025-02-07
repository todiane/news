import os
import sys
from pathlib import Path
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

# Add project root to Python path BEFORE any app imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = str(Path(current_dir).parent.parent)
sys.path.insert(0, project_root)

# Now we can import app modules
from app.core.background_tasks import background_task_manager
from app.core.cache import CacheManager
from main import app
from app.db.base import get_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[TestClient, None]:
    """Create a test client for integration tests."""
    async with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[Session, None]:
    """Get a test database session."""
    async with get_db() as session:
        yield session

@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear cache before each test."""
    cache = CacheManager()
    cache.clear()
    yield
    cache.clear()

@pytest.fixture(autouse=True)
async def stop_background_tasks():
    """Stop background tasks after each test."""
    yield
    await background_task_manager.stop()

@pytest.fixture
def mock_feed_fetcher(monkeypatch):
    """Fixture to mock feed fetcher for integration tests."""
    class MockFeedFetcher:
        async def fetch_feed(self, url: str):
            return []
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    monkeypatch.setattr("app.core.feed_fetcher.FeedFetcher", MockFeedFetcher)
    return MockFeedFetcher()

@pytest.fixture
def mock_notification_manager(monkeypatch):
    """Fixture to mock notification manager for integration tests."""
    class MockNotificationManager:
        async def notify_feed_updates(self, *args, **kwargs):
            pass
    
    monkeypatch.setattr("app.core.notification_manager.notification_manager", MockNotificationManager())
    return MockNotificationManager()

@pytest.fixture
def mock_background_tasks(monkeypatch):
    """Fixture to mock background tasks for integration tests."""
    class MockBackgroundTasks:
        async def start_feed_refresh_task(self, *args, **kwargs):
            pass
            
        async def stop(self):
            pass
    
    monkeypatch.setattr("app.core.background_tasks.background_task_manager", MockBackgroundTasks())
    return MockBackgroundTasks()

@pytest.fixture
def mock_redis(monkeypatch):
    """Fixture to mock Redis for integration tests."""
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        def get(self, key):
            return self.data.get(key)
            
        def set(self, key, value, ex=None):
            self.data[key] = value
            
        def delete(self, key):
            self.data.pop(key, None)
            
        def flushdb(self):
            self.data.clear()
    
    monkeypatch.setattr("redis.Redis", lambda *args, **kwargs: MockRedis())
    return MockRedis()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user import User
from app.models.feed import Feed
from app.models.feed_preference import FeedPreference
from app.core.notification_manager import NotificationManager

@pytest.fixture
def test_feed(db: Session, test_user: User):
    """Create a test feed."""
    feed = Feed(
        name="Test Feed",
        url="http://example.com/feed.xml",
        feed_type="rss",
        category="tech",
        user_id=test_user.id
    )
    db.add(feed)
    db.commit()
    db.refresh(feed)
    return feed

@pytest.fixture
def test_preference(db: Session, test_user: User, test_feed: Feed):
    """Create a test feed preference."""
    pref = FeedPreference(
        user_id=test_user.id,
        feed_id=test_feed.id,
        is_favorite=False,
        notification_enabled=True,
        update_frequency="daily",
        categories=["tech", "news"]
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref

def test_create_preference(client: TestClient, test_user: User, test_feed: Feed):
    """Test creating a new feed preference."""
    response = client.post(
        "/api/v1/subscriptions/preferences",
        json={
            "feed_id": test_feed.id,
            "is_favorite": True,
            "notification_enabled": True,
            "update_frequency": "realtime",
            "categories": ["tech"]
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["feed_id"] == test_feed.id
    assert data["is_favorite"] is True
    assert data["notification_enabled"] is True
    assert data["update_frequency"] == "realtime"
    assert "tech" in data["categories"]

def test_get_preferences(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test retrieving user's feed preferences."""
    response = client.get(
        "/api/v1/subscriptions/preferences",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["feed_id"] == test_preference.feed_id

def test_update_preference(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test updating feed preferences."""
    response = client.put(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}",
        json={
            "is_favorite": True,
            "notification_enabled": False,
            "update_frequency": "weekly",
            "categories": ["tech", "ai"]
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] is True
    assert data["notification_enabled"] is False
    assert data["update_frequency"] == "weekly"
    assert "ai" in data["categories"]

def test_mark_article_read(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test marking an article as read."""
    article_id = "test-article-1"
    response = client.post(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}/read/{article_id}",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify the article is marked as read
    pref_response = client.get(
        "/api/v1/subscriptions/preferences",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    data = pref_response.json()
    read_items = next(p["read_items"] for p in data if p["feed_id"] == test_preference.feed_id)
    assert article_id in read_items

def test_toggle_bookmark(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test toggling article bookmark status."""
    article_id = "test-article-1"
    
    # Add bookmark
    response = client.post(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}/bookmark/{article_id}",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert response.json()["bookmarked"] is True

    # Remove bookmark
    response = client.post(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}/bookmark/{article_id}",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert response.json()["bookmarked"] is False

def test_notification_settings(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test notification settings update and validation."""
    # Test invalid frequency
    response = client.put(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}",
        json={
            "notification_enabled": True,
            "update_frequency": "invalid_frequency"
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 422  # Validation error

    # Test valid frequency
    response = client.put(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}",
        json={
            "notification_enabled": True,
            "update_frequency": "hourly"
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert response.json()["update_frequency"] == "hourly"

def test_category_management(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test category management for feed preferences."""
    # Add new category
    response = client.put(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}",
        json={
            "categories": ["tech", "news", "ai"]
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert "ai" in response.json()["categories"]

    # Remove category
    response = client.put(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}",
        json={
            "categories": ["tech", "news"]
        },
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    assert "ai" not in response.json()["categories"]

def test_reading_progress(client: TestClient, test_user: User, test_preference: FeedPreference):
    """Test tracking reading progress."""
    article_id = "test-article-1"
    
    # Mark article as in progress
    response = client.post(
        f"/api/v1/subscriptions/preferences/{test_preference.feed_id}/progress/{article_id}",
        json={"position": 0.5},
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    assert response.status_code == 200
    
    # Verify progress is saved
    pref_response = client.get(
        "/api/v1/subscriptions/preferences",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    data = pref_response.json()
    progress = next(p["reading_progress"] for p in data if p["feed_id"] == test_preference.feed_id)
    assert article_id in progress
    assert progress[article_id]["position"] == 0.5

def test_preference_cleanup(client: TestClient, test_user: User, test_preference: FeedPreference, db: Session):
    """Test preference cleanup when feed is deleted."""
    # Delete feed
    feed_id = test_preference.feed_id
    db.delete(test_preference.feed)
    db.commit()

    # Verify preference is also deleted
    response = client.get(
        "/api/v1/subscriptions/preferences",
        headers={"Authorization": f"Bearer {test_user.create_access_token()}"}
    )
    data = response.json()
    assert not any(p["feed_id"] == feed_id for p in data)
    
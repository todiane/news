# tests/test_feed_management.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.feed import Feed
from app.models.feed_preference import FeedPreference
from app.core.notification_manager import NotificationManager

def test_create_feed(client: TestClient, db: Session, normal_user_token_headers):
    response = client.post(
        "/api/v1/feeds/",
        headers=normal_user_token_headers,
        json={
            "name": "Test Feed",
            "url": "http://example.com/feed.xml",
            "category": "tech"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Feed"
    assert data["url"] == "http://example.com/feed.xml"

def test_update_feed_preferences(client: TestClient, db: Session, normal_user_token_headers):
    # First create a feed
    feed_response = client.post(
        "/api/v1/feeds/",
        headers=normal_user_token_headers,
        json={
            "name": "Test Feed",
            "url": "http://example.com/feed.xml",
            "category": "tech"
        }
    )
    feed_id = feed_response.json()["id"]

    # Update preferences
    response = client.put(
        f"/api/v1/subscriptions/preferences/{feed_id}",
        headers=normal_user_token_headers,
        json={
            "is_favorite": True,
            "notification_enabled": True,
            "update_frequency": "daily",
            "categories": ["tech", "news"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] == True
    assert data["update_frequency"] == "daily"

def test_bookmark_article(client: TestClient, db: Session, normal_user_token_headers):
    # Create feed and article first
    feed_id = 1
    article_id = "test-article"

    response = client.post(
        f"/api/v1/subscriptions/preferences/{feed_id}/bookmark/{article_id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["bookmarked"] == True

def test_notification_frequency(client: TestClient, db: Session):
    notification_manager = NotificationManager()
    pref = FeedPreference(
        update_frequency="hourly",
        last_notification_sent=datetime.utcnow()
    )
    assert notification_manager._should_send_notification(pref) == False

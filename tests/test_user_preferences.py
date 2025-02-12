import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.security import create_access_token
from app.models.user import User
from app.core.config import settings

@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$LQgXxGNhDlN0QMf5ORf6aOYz6TtxMQJqhN.B4bf.tg0WdHkE4OYmO",  # "testpassword"
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def inactive_user(db: Session):
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password="$2b$12$LQgXxGNhDlN0QMf5ORf6aOYz6TtxMQJqhN.B4bf.tg0WdHkE4OYmO",
        is_active=False,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def unverified_user(db: Session):
    """Create an unverified test user."""
    user = User(
        email="unverified@example.com",
        hashed_password="$2b$12$LQgXxGNhDlN0QMf5ORf6aOYz6TtxMQJqhN.B4bf.tg0WdHkE4OYmO",
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_login_success(client: TestClient, test_user: User):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

def test_login_invalid_credentials(client: TestClient, test_user: User):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "access_token" not in response.json()

def test_login_inactive_user(client: TestClient, inactive_user: User):
    """Test login attempt with inactive user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": inactive_user.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 400
    assert "inactive user" in response.json()["detail"].lower()

def test_login_unverified_user(client: TestClient, unverified_user: User):
    """Test login attempt with unverified user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": unverified_user.email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 400
    assert "not verified" in response.json()["detail"].lower()

def test_register_user(client: TestClient, db: Session):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPass123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert "message" in data
    assert "verification" in data["message"].lower()

def test_register_existing_email(client: TestClient, test_user: User):
    """Test registration with existing email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "StrongPass123!"
        }
    )
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()

def test_verify_email(client: TestClient, db: Session):
    """Test email verification."""
    # Create unverified user
    user = User(
        email="toverify@example.com",
        hashed_password="$2b$12$LQgXxGNhDlN0QMf5ORf6aOYz6TtxMQJqhN.B4bf.tg0WdHkE4OYmO",
        is_active=True,
        is_verified=False,
        verification_token="valid_token"
    )
    db.add(user)
    db.commit()

    response = client.post("/api/v1/auth/verify-email/valid_token")
    assert response.status_code == 200
    assert "verified" in response.json()["message"].lower()

    # Check user is now verified
    db.refresh(user)
    assert user.is_verified is True

def test_verify_email_invalid_token(client: TestClient):
    """Test email verification with invalid token."""
    response = client.post("/api/v1/auth/verify-email/invalid_token")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

def test_refresh_token(client: TestClient, test_user: User):
    """Test token refresh."""
    # First get an access token and refresh token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    
    # Get refresh token from cookie
    refresh_token = login_response.cookies.get("refresh_token")
    assert refresh_token is not None

    # Try to refresh token
    response = client.post(
        "/api/v1/auth/refresh-token",
        cookies={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_logout(client: TestClient, test_user: User):
    """Test logout functionality."""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "refresh_token" not in response.cookies

def test_password_strength(client: TestClient):
    """Test password strength validation during registration."""
    weak_passwords = [
        "short",  # Too short
        "nouppercaseornumbers",  # No uppercase or numbers
        "NoSpecialChars123",  # No special characters
        "NoNumbers!",  # No numbers
    ]

    for password in weak_passwords:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": password
            }
        )
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
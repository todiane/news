# backend/tests/conftest.py

import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Fix path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # Get backend directory
sys.path.insert(0, backend_dir)  # Add backend to path

# Import after path setup
from app.db.base_class import Base
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
try:
    from backend.main import app  # Try to import from backend main.py first
except ImportError:
    from main import app  # Fallback to app.main if needed

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides["get_db"] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def normal_user_token_headers(client: TestClient, db: Session):
    """Return a valid token for normal user"""
    user = User(
        email="test@example.com",
        hashed_password="testpass",
        is_active=True
    )
    db.add(user)
    db.commit()
    
    access_token = create_access_token(user.id)
    return {"Authorization": f"Bearer {access_token}"}

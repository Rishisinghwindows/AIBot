"""
Pytest configuration and fixtures for OhGrt API tests.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.config import Settings, get_settings
from app.db.base import Base, SessionLocal, get_db
from app.db.models import User, RefreshToken, ChatMessage
from app.main import app


# Test database URL (SQLite in-memory for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="development",
        jwt_secret_key="test-secret-key-for-testing-only",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_user="test",
        postgres_password="test",
        postgres_db="test",
        rate_limit_enabled=False,
        cors_origins="*",
    )


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create test client with overridden dependencies."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# User fixtures
@pytest.fixture
def test_user(test_db) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        firebase_uid="test-firebase-uid-123",
        email="test@example.com",
        display_name="Test User",
        photo_url="https://example.com/photo.jpg",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_with_refresh_token(test_db, test_user, test_settings) -> tuple[User, str]:
    """Create a test user with a valid refresh token."""
    import hashlib

    token = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    refresh_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=test_user.id,
        token_hash=token_hash,
        device_info="test-device",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    test_db.add(refresh_token)
    test_db.commit()

    return test_user, token


@pytest.fixture
def auth_headers(test_user, test_settings) -> dict:
    """Create authentication headers with valid JWT."""
    from app.auth.jwt_handler import JWTHandler

    jwt_handler = JWTHandler(test_settings)
    access_token = jwt_handler.create_access_token(
        user_id=str(test_user.id),
        email=test_user.email,
    )

    return {
        "Authorization": f"Bearer {access_token}",
        "X-Request-ID": str(uuid.uuid4()),
        "X-Nonce": str(uuid.uuid4()),
        "X-Timestamp": str(int(datetime.now(timezone.utc).timestamp())),
    }


@pytest.fixture
def security_headers() -> dict:
    """Create security headers without auth."""
    return {
        "X-Request-ID": str(uuid.uuid4()),
        "X-Nonce": str(uuid.uuid4()),
        "X-Timestamp": str(int(datetime.now(timezone.utc).timestamp())),
    }


# Mock fixtures
@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK."""
    with patch("app.auth.firebase.firebase_admin") as mock:
        mock.get_app.return_value = MagicMock()
        mock.auth.verify_id_token.return_value = {
            "uid": "test-firebase-uid-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }
        yield mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("app.utils.llm.ChatOpenAI") as mock:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Test response")
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_httpx():
    """Mock httpx client for external API calls."""
    with patch("httpx.AsyncClient") as mock:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"data": "test"},
        )
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock.return_value = mock_instance
        yield mock


# Chat fixtures
@pytest.fixture
def test_conversation_id() -> uuid.UUID:
    """Generate a test conversation ID."""
    return uuid.uuid4()


@pytest.fixture
def test_messages(test_db, test_user, test_conversation_id) -> list[ChatMessage]:
    """Create test chat messages."""
    messages = [
        ChatMessage(
            id=uuid.uuid4(),
            user_id=test_user.id,
            conversation_id=test_conversation_id,
            role="user",
            content="Hello, how are you?",
        ),
        ChatMessage(
            id=uuid.uuid4(),
            user_id=test_user.id,
            conversation_id=test_conversation_id,
            role="assistant",
            content="I'm doing well, thank you! How can I help you today?",
        ),
    ]
    for msg in messages:
        test_db.add(msg)
    test_db.commit()
    return messages

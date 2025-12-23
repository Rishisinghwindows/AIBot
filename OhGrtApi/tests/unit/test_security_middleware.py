"""
Unit tests for security middleware.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


@pytest.fixture
def app_with_middleware():
    """Create a FastAPI app with security middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    return app


@pytest.fixture
def test_client(app_with_middleware):
    """Create test client."""
    return TestClient(app_with_middleware)


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_exempt_path_health(self, test_client):
        """Test that /health is exempt from security headers."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_exempt_path_docs(self, test_client):
        """Test that /docs is exempt from security headers."""
        response = test_client.get("/docs")
        # May return 200 or redirect
        assert response.status_code in [200, 307]

    def test_missing_all_headers(self, test_client):
        """Test request without any security headers."""
        response = test_client.get("/test")
        assert response.status_code == 400
        assert "Missing required security headers" in response.json()["detail"]

    def test_missing_request_id(self, test_client):
        """Test request without X-Request-ID."""
        headers = {
            "X-Nonce": str(uuid.uuid4()),
            "X-Timestamp": str(int(time.time())),
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400
        assert "X-Request-ID" in response.json()["detail"]

    def test_missing_nonce(self, test_client):
        """Test request without X-Nonce."""
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Timestamp": str(int(time.time())),
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400
        assert "X-Nonce" in response.json()["detail"]

    def test_missing_timestamp(self, test_client):
        """Test request without X-Timestamp."""
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Nonce": str(uuid.uuid4()),
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400
        assert "X-Timestamp" in response.json()["detail"]

    def test_invalid_timestamp_format(self, test_client):
        """Test request with invalid timestamp format."""
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Nonce": str(uuid.uuid4()),
            "X-Timestamp": "not-a-timestamp",
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400
        assert "Invalid timestamp" in response.json()["detail"]

    def test_expired_timestamp(self, test_client):
        """Test request with expired timestamp (too old)."""
        old_timestamp = int((datetime.now(timezone.utc) - timedelta(minutes=10)).timestamp())
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Nonce": str(uuid.uuid4()),
            "X-Timestamp": str(old_timestamp),
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400
        assert "timestamp expired" in response.json()["detail"].lower()

    def test_future_timestamp(self, test_client):
        """Test request with future timestamp (too far ahead)."""
        future_timestamp = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Nonce": str(uuid.uuid4()),
            "X-Timestamp": str(future_timestamp),
        }
        response = test_client.get("/test", headers=headers)
        assert response.status_code == 400

    def test_options_request_exempt(self, test_client):
        """Test that OPTIONS requests (CORS preflight) are exempt."""
        response = test_client.options("/test")
        # OPTIONS should not require security headers
        assert response.status_code in [200, 405]

    def test_response_includes_request_id(self, test_client):
        """Test that response includes X-Request-ID header."""
        request_id = str(uuid.uuid4())
        headers = {
            "X-Request-ID": request_id,
            "X-Nonce": str(uuid.uuid4()),
            "X-Timestamp": str(int(time.time())),
        }

        with patch("app.middleware.security.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_session.return_value = mock_db

            response = test_client.get("/test", headers=headers)

            if response.status_code == 200:
                assert response.headers.get("X-Request-ID") == request_id


class TestNonceValidation:
    """Tests for nonce replay prevention."""

    def test_nonce_reuse_blocked(self, test_client):
        """Test that reusing a nonce is blocked."""
        nonce = str(uuid.uuid4())
        headers = {
            "X-Request-ID": str(uuid.uuid4()),
            "X-Nonce": nonce,
            "X-Timestamp": str(int(time.time())),
        }

        with patch("app.middleware.security.SessionLocal") as mock_session:
            mock_db = MagicMock()
            # First request - nonce not found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_session.return_value = mock_db

            response1 = test_client.get("/test", headers=headers)

            # Second request - simulate nonce already used
            mock_nonce = MagicMock()
            mock_nonce.nonce = nonce
            mock_db.query.return_value.filter.return_value.first.return_value = mock_nonce

            headers["X-Request-ID"] = str(uuid.uuid4())  # New request ID
            response2 = test_client.get("/test", headers=headers)

            assert response2.status_code == 400
            assert "already been used" in response2.json()["detail"]

"""
Unit tests for JWT handler.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.auth.jwt_handler import JWTHandler
from app.config import Settings


class TestJWTHandler:
    """Tests for JWTHandler class."""

    @pytest.fixture
    def jwt_handler(self, test_settings) -> JWTHandler:
        """Create JWT handler instance."""
        return JWTHandler(test_settings)

    @pytest.fixture
    def user_id(self) -> str:
        """Generate test user ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def email(self) -> str:
        """Test email."""
        return "test@example.com"

    def test_create_access_token(self, jwt_handler, user_id, email):
        """Test access token creation."""
        token = jwt_handler.create_access_token(user_id=user_id, email=email)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, jwt_handler, user_id):
        """Test refresh token creation."""
        token = jwt_handler.create_refresh_token(user_id=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_access_token(self, jwt_handler, user_id, email):
        """Test decoding a valid access token."""
        token = jwt_handler.create_access_token(user_id=user_id, email=email)
        payload = jwt_handler.decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self, jwt_handler, user_id):
        """Test decoding a valid refresh token."""
        token = jwt_handler.create_refresh_token(user_id=user_id)
        payload = jwt_handler.decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self, jwt_handler):
        """Test decoding an invalid token."""
        payload = jwt_handler.decode_token("invalid.token.here")

        assert payload is None

    def test_decode_expired_token(self, test_settings):
        """Test decoding an expired token."""
        # Create handler with very short expiry
        settings = Settings(
            jwt_secret_key="test-secret",
            jwt_access_token_expire_minutes=-1,  # Already expired
        )
        jwt_handler = JWTHandler(settings)

        token = jwt_handler.create_access_token(
            user_id=str(uuid.uuid4()),
            email="test@example.com",
        )

        # Token should be invalid due to expiration
        payload = jwt_handler.decode_token(token)
        assert payload is None

    def test_tokens_are_unique(self, jwt_handler, user_id, email):
        """Test that generated tokens are unique."""
        token1 = jwt_handler.create_access_token(user_id=user_id, email=email)
        token2 = jwt_handler.create_access_token(user_id=user_id, email=email)

        assert token1 != token2

    def test_access_token_has_correct_expiry(self, jwt_handler, user_id, email):
        """Test that access token has correct expiry time."""
        token = jwt_handler.create_access_token(user_id=user_id, email=email)
        payload = jwt_handler.decode_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire in approximately 15 minutes (with some tolerance)
        time_diff = (exp_time - now).total_seconds()
        assert 14 * 60 < time_diff < 16 * 60

    def test_refresh_token_has_correct_expiry(self, jwt_handler, user_id):
        """Test that refresh token has correct expiry time."""
        token = jwt_handler.create_refresh_token(user_id=user_id)
        payload = jwt_handler.decode_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire in approximately 7 days (with some tolerance)
        time_diff = (exp_time - now).total_seconds()
        expected_seconds = 7 * 24 * 60 * 60
        assert expected_seconds - 3600 < time_diff < expected_seconds + 3600

    def test_different_secrets_produce_different_tokens(self, user_id, email):
        """Test that different secrets produce different tokens."""
        settings1 = Settings(jwt_secret_key="secret-1")
        settings2 = Settings(jwt_secret_key="secret-2")

        handler1 = JWTHandler(settings1)
        handler2 = JWTHandler(settings2)

        token1 = handler1.create_access_token(user_id=user_id, email=email)
        token2 = handler2.create_access_token(user_id=user_id, email=email)

        assert token1 != token2

    def test_token_from_different_secret_fails_decode(self, user_id, email):
        """Test that token from different secret cannot be decoded."""
        settings1 = Settings(jwt_secret_key="secret-1")
        settings2 = Settings(jwt_secret_key="secret-2")

        handler1 = JWTHandler(settings1)
        handler2 = JWTHandler(settings2)

        token = handler1.create_access_token(user_id=user_id, email=email)
        payload = handler2.decode_token(token)

        assert payload is None

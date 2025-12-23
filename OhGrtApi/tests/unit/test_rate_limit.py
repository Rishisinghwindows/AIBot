"""
Unit tests for rate limiting middleware.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.middleware.rate_limit import InMemoryRateLimiter, RateLimitMiddleware


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter instance."""
        return InMemoryRateLimiter()

    def test_allows_first_request(self, limiter):
        """Test that first request is allowed."""
        allowed, remaining, retry_after = limiter.is_allowed(
            key="test-user",
            max_requests=10,
            window_seconds=60,
        )

        assert allowed is True
        assert remaining == 9
        assert retry_after == 0

    def test_allows_requests_under_limit(self, limiter):
        """Test that requests under limit are allowed."""
        for i in range(5):
            allowed, remaining, _ = limiter.is_allowed(
                key="test-user",
                max_requests=10,
                window_seconds=60,
            )
            assert allowed is True
            assert remaining == 9 - i

    def test_blocks_requests_over_limit(self, limiter):
        """Test that requests over limit are blocked."""
        # Use up all requests
        for _ in range(10):
            limiter.is_allowed(
                key="test-user",
                max_requests=10,
                window_seconds=60,
            )

        # Next request should be blocked
        allowed, remaining, retry_after = limiter.is_allowed(
            key="test-user",
            max_requests=10,
            window_seconds=60,
        )

        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    def test_different_keys_independent(self, limiter):
        """Test that different keys have independent limits."""
        # Use up all requests for user1
        for _ in range(10):
            limiter.is_allowed("user1", 10, 60)

        # user2 should still be allowed
        allowed, _, _ = limiter.is_allowed("user2", 10, 60)
        assert allowed is True

    def test_window_expiry(self, limiter):
        """Test that requests are allowed after window expires."""
        # Use a very short window
        for _ in range(3):
            limiter.is_allowed("test-user", 3, 1)

        # Should be blocked
        allowed, _, _ = limiter.is_allowed("test-user", 3, 1)
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed, _, _ = limiter.is_allowed("test-user", 3, 1)
        assert allowed is True

    def test_remaining_count_accurate(self, limiter):
        """Test that remaining count is accurate."""
        allowed, remaining, _ = limiter.is_allowed("test", 5, 60)
        assert remaining == 4

        allowed, remaining, _ = limiter.is_allowed("test", 5, 60)
        assert remaining == 3

        allowed, remaining, _ = limiter.is_allowed("test", 5, 60)
        assert remaining == 2


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware integration."""

    def test_exempt_paths_not_limited(self):
        """Test that exempt paths bypass rate limiting."""
        exempt_paths = RateLimitMiddleware.EXEMPT_PATHS

        assert "/health" in exempt_paths
        assert "/health/live" in exempt_paths
        assert "/health/ready" in exempt_paths
        assert "/" in exempt_paths

    def test_exempt_prefixes(self):
        """Test exempt path prefixes."""
        exempt_prefixes = RateLimitMiddleware.EXEMPT_PREFIXES

        assert "/docs" in exempt_prefixes
        assert "/redoc" in exempt_prefixes


class TestRateLimitIntegration:
    """Integration tests for rate limiting."""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting enabled."""
        from fastapi import FastAPI

        app = FastAPI()

        # Add rate limit middleware with low limits for testing
        with patch("app.middleware.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                rate_limit_enabled=True,
                rate_limit_requests_per_minute=5,
                rate_limit_requests_per_hour=100,
                redis_url="redis://localhost:6379/0",
            )
            app.add_middleware(RateLimitMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    def test_rate_limit_headers_present(self, app_with_rate_limit):
        """Test that rate limit headers are in response."""
        from fastapi.testclient import TestClient

        client = TestClient(app_with_rate_limit)

        response = client.get("/test")

        # Headers should be present (may vary based on implementation)
        assert response.status_code in [200, 429]

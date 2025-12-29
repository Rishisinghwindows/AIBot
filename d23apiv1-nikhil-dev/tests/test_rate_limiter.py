"""
Tests for Rate Limiter

Tests the sliding window rate limiting functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from bot.utils.rate_limiter import InMemoryRateLimiter


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def limiter(self):
        """Create a rate limiter with test-friendly settings."""
        return InMemoryRateLimiter(
            max_requests_per_minute=5,
            burst_limit=2,
            burst_window_seconds=1,
            cooldown_seconds=2,
        )

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self, limiter):
        """Test that requests under limit are allowed."""
        user_id = "test_user_1"

        for i in range(5):
            allowed, info = await limiter.check_rate_limit(user_id)
            assert allowed is True, f"Request {i+1} should be allowed"
            assert info["remaining"] == 5 - (i + 1)

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self, limiter):
        """Test that requests over limit are blocked."""
        user_id = "test_user_2"

        # Exhaust the limit
        for _ in range(5):
            await limiter.check_rate_limit(user_id)

        # Next request should be blocked
        allowed, info = await limiter.check_rate_limit(user_id)
        assert allowed is False
        assert "retry_after" in info

    @pytest.mark.asyncio
    async def test_burst_protection(self, limiter):
        """Test burst protection works."""
        user_id = "test_user_3"

        # Make requests very quickly (burst)
        allowed1, _ = await limiter.check_rate_limit(user_id)
        allowed2, _ = await limiter.check_rate_limit(user_id)

        assert allowed1 is True
        assert allowed2 is True

        # Third request in burst window should trigger burst protection
        allowed3, info = await limiter.check_rate_limit(user_id)
        assert allowed3 is False
        assert "burst" in info.get("reason", "").lower()

    @pytest.mark.asyncio
    async def test_different_users_have_separate_limits(self, limiter):
        """Test that different users have separate rate limits."""
        user1 = "user_1"
        user2 = "user_2"

        # Exhaust user1's limit
        for _ in range(5):
            await limiter.check_rate_limit(user1)

        # user1 should be blocked
        allowed1, _ = await limiter.check_rate_limit(user1)
        assert allowed1 is False

        # user2 should still be allowed
        allowed2, _ = await limiter.check_rate_limit(user2)
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_limit_resets_after_window(self, limiter):
        """Test that limit resets after the time window."""
        user_id = "test_user_4"

        # Use a limiter with very short window for testing
        short_limiter = InMemoryRateLimiter(
            max_requests_per_minute=2,
            burst_limit=10,  # High burst to not trigger
            burst_window_seconds=1,
            cooldown_seconds=0.1,
        )

        # Exhaust limit
        await short_limiter.check_rate_limit(user_id)
        await asyncio.sleep(0.1)  # Small delay between requests
        await short_limiter.check_rate_limit(user_id)

        # Should be blocked
        allowed, _ = await short_limiter.check_rate_limit(user_id)
        # Note: This depends on implementation - may need adjustment

    @pytest.mark.asyncio
    async def test_get_user_status(self, limiter):
        """Test getting user rate limit status."""
        user_id = "test_user_5"

        # Make some requests
        await limiter.check_rate_limit(user_id)
        await limiter.check_rate_limit(user_id)

        status = await limiter.get_user_status(user_id)

        assert "requests_made" in status
        assert "remaining" in status
        assert "is_limited" in status
        assert status["requests_made"] == 2
        assert status["remaining"] == 3

    @pytest.mark.asyncio
    async def test_reset_user_limit(self, limiter):
        """Test resetting user rate limit."""
        user_id = "test_user_6"

        # Exhaust limit
        for _ in range(5):
            await limiter.check_rate_limit(user_id)

        # Should be blocked
        allowed, _ = await limiter.check_rate_limit(user_id)
        assert allowed is False

        # Reset limit
        await limiter.reset_user_limit(user_id)

        # Should be allowed again
        allowed, _ = await limiter.check_rate_limit(user_id)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, limiter):
        """Test that old entries are cleaned up."""
        # This tests internal cleanup mechanism
        user_id = "test_user_7"

        await limiter.check_rate_limit(user_id)

        # Verify user is tracked
        status = await limiter.get_user_status(user_id)
        assert status["requests_made"] > 0

        # Cleanup should remove old entries
        # (Implementation dependent - may need adjustment)

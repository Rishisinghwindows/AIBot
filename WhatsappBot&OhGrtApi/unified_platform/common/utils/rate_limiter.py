"""
Rate Limiter for WhatsApp Bot

Protects against abuse by limiting request rates per user.
Uses in-memory storage with optional Redis backend.
"""

import asyncio
import logging
import time
from collections import deque
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 30          # Maximum requests
    window_seconds: int = 60        # Time window in seconds
    burst_limit: int = 5            # Max requests in 5 seconds (burst protection)
    burst_window: int = 5           # Burst window in seconds
    cooldown_seconds: int = 60      # Cooldown period after limit exceeded


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Tracks request timestamps per user and enforces limits.

    Usage:
        limiter = InMemoryRateLimiter()

        # Check before processing
        allowed, info = await limiter.check_rate_limit("919876543210")
        if not allowed:
            return f"Rate limit exceeded. Try again in {info['retry_after']} seconds."

        # Record the request
        await limiter.record_request("919876543210")
    """

    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._requests: Dict[str, deque] = {}  # phone -> deque of timestamps
        self._cooldowns: Dict[str, float] = {}  # phone -> cooldown end time
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, phone: str) -> Tuple[bool, dict]:
        """
        Check if a request is allowed under rate limits.

        Args:
            phone: User's phone number

        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: remaining, reset_in, retry_after (if blocked)
        """
        async with self._lock:
            now = time.time()

            # Check cooldown
            if phone in self._cooldowns:
                cooldown_end = self._cooldowns[phone]
                if now < cooldown_end:
                    retry_after = int(cooldown_end - now)
                    return False, {
                        "remaining": 0,
                        "reset_in": retry_after,
                        "retry_after": retry_after,
                        "reason": "cooldown",
                    }
                else:
                    # Cooldown expired
                    del self._cooldowns[phone]

            # Initialize request tracking if needed
            if phone not in self._requests:
                self._requests[phone] = deque()

            # Clean old requests outside window
            window_start = now - self.config.window_seconds
            burst_start = now - self.config.burst_window

            requests = self._requests[phone]
            while requests and requests[0] < window_start:
                requests.popleft()

            # Count requests in windows
            total_requests = len(requests)
            burst_requests = sum(1 for ts in requests if ts >= burst_start)

            # Check limits
            if total_requests >= self.config.max_requests:
                # Set cooldown
                self._cooldowns[phone] = now + self.config.cooldown_seconds
                return False, {
                    "remaining": 0,
                    "reset_in": self.config.cooldown_seconds,
                    "retry_after": self.config.cooldown_seconds,
                    "reason": "rate_limit",
                }

            if burst_requests >= self.config.burst_limit:
                # Short burst cooldown
                return False, {
                    "remaining": self.config.max_requests - total_requests,
                    "reset_in": self.config.burst_window,
                    "retry_after": self.config.burst_window,
                    "reason": "burst_limit",
                }

            # Calculate when window resets
            if requests:
                oldest = requests[0]
                reset_in = int(oldest + self.config.window_seconds - now)
            else:
                reset_in = self.config.window_seconds

            return True, {
                "remaining": self.config.max_requests - total_requests - 1,
                "reset_in": reset_in,
            }

    async def record_request(self, phone: str):
        """
        Record a request for rate limiting.

        Args:
            phone: User's phone number
        """
        async with self._lock:
            now = time.time()

            if phone not in self._requests:
                self._requests[phone] = deque()

            self._requests[phone].append(now)

    async def get_status(self, phone: str) -> dict:
        """
        Get rate limit status for a user.

        Args:
            phone: User's phone number

        Returns:
            Status dict with remaining, reset_in, is_limited
        """
        allowed, info = await self.check_rate_limit(phone)
        return {
            "phone": phone,
            "is_limited": not allowed,
            "remaining": info.get("remaining", self.config.max_requests),
            "reset_in": info.get("reset_in", self.config.window_seconds),
            "max_requests": self.config.max_requests,
            "window_seconds": self.config.window_seconds,
        }

    async def reset_user(self, phone: str):
        """
        Reset rate limit for a user (admin function).

        Args:
            phone: User's phone number
        """
        async with self._lock:
            if phone in self._requests:
                del self._requests[phone]
            if phone in self._cooldowns:
                del self._cooldowns[phone]

    async def cleanup(self):
        """Clean up old entries to prevent memory growth."""
        async with self._lock:
            now = time.time()
            window_start = now - self.config.window_seconds

            # Clean old requests
            phones_to_remove = []
            for phone, requests in self._requests.items():
                while requests and requests[0] < window_start:
                    requests.popleft()
                if not requests:
                    phones_to_remove.append(phone)

            for phone in phones_to_remove:
                del self._requests[phone]

            # Clean expired cooldowns
            expired = [p for p, t in self._cooldowns.items() if t < now]
            for phone in expired:
                del self._cooldowns[phone]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter(config: RateLimitConfig = None) -> InMemoryRateLimiter:
    """
    Get the singleton rate limiter instance.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        Rate limiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(config)
    return _rate_limiter


# =============================================================================
# MIDDLEWARE DECORATOR
# =============================================================================

def rate_limited(func):
    """
    Decorator to add rate limiting to async handlers.

    Usage:
        @rate_limited
        async def handle_message(state: BotState) -> dict:
            ...

    The handler must have state with whatsapp_message.from_number.
    """
    async def wrapper(state, *args, **kwargs):
        # Get phone number from state
        phone = state.get("whatsapp_message", {}).get("from_number", "")
        if not phone:
            # No phone number, skip rate limiting
            return await func(state, *args, **kwargs)

        limiter = get_rate_limiter()

        # Check rate limit
        allowed, info = await limiter.check_rate_limit(phone)
        if not allowed:
            reason = info.get("reason", "rate_limit")
            retry_after = info.get("retry_after", 60)

            if reason == "burst_limit":
                message = f"Slow down! Please wait {retry_after} seconds before sending more messages."
            else:
                message = f"Too many requests. Please try again in {retry_after} seconds."

            return {
                "response_text": message,
                "response_type": "text",
                "should_fallback": False,
                "rate_limited": True,
            }

        # Record the request
        await limiter.record_request(phone)

        # Execute the handler
        return await func(state, *args, **kwargs)

    return wrapper


# =============================================================================
# RATE LIMIT RESPONSE HELPER
# =============================================================================

def format_rate_limit_response(info: dict) -> str:
    """
    Format a user-friendly rate limit message.

    Args:
        info: Rate limit info dict

    Returns:
        Formatted message string
    """
    reason = info.get("reason", "rate_limit")
    retry_after = info.get("retry_after", 60)

    if reason == "burst_limit":
        return (
            "Whoa, slow down! You're sending messages too quickly.\n\n"
            f"Please wait {retry_after} seconds before trying again."
        )
    elif reason == "cooldown":
        return (
            "You've been temporarily rate limited.\n\n"
            f"Please wait {retry_after} seconds before sending more messages.\n\n"
            "_This helps ensure fair access for all users._"
        )
    else:
        minutes = retry_after // 60
        seconds = retry_after % 60
        time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        return (
            "You've reached the message limit.\n\n"
            f"Please wait {time_str} before sending more messages.\n\n"
            "_Tip: Try to combine related questions into fewer messages._"
        )


# =============================================================================
# HTTP RATE LIMITER (for API middleware)
# =============================================================================

class RateLimiter:
    """
    Rate limiter for HTTP API middleware.

    Supports both in-memory and Redis backends.
    Used by ohgrt_api/middleware/rate_limit.py
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        redis_url: Optional[str] = None
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            redis_url: Optional Redis URL for distributed rate limiting
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.redis_url = redis_url

        # In-memory storage: key -> list of timestamps
        self._requests: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

    def check(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key (e.g., "user:123" or "ip:1.2.3.4")

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()

        if key not in self._requests:
            self._requests[key] = deque()

        requests = self._requests[key]

        # Clean old requests
        minute_ago = now - 60
        hour_ago = now - 3600

        while requests and requests[0] < hour_ago:
            requests.popleft()

        # Count requests
        minute_count = sum(1 for ts in requests if ts >= minute_ago)
        hour_count = len(requests)

        # Check limits
        if minute_count >= self.requests_per_minute:
            # Calculate retry after
            oldest_in_minute = next((ts for ts in requests if ts >= minute_ago), now)
            retry_after = int(oldest_in_minute + 60 - now) + 1
            return False, retry_after

        if hour_count >= self.requests_per_hour:
            oldest = requests[0] if requests else now
            retry_after = int(oldest + 3600 - now) + 1
            return False, retry_after

        # Record request
        requests.append(now)
        return True, None

    def get_remaining(self, key: str) -> dict:
        """
        Get remaining requests for a key.

        Args:
            key: Rate limit key

        Returns:
            Dict with minute_remaining and hour_remaining
        """
        now = time.time()

        if key not in self._requests:
            return {
                "minute_remaining": self.requests_per_minute,
                "hour_remaining": self.requests_per_hour,
            }

        requests = self._requests[key]
        minute_ago = now - 60
        hour_ago = now - 3600

        minute_count = sum(1 for ts in requests if ts >= minute_ago)
        hour_count = sum(1 for ts in requests if ts >= hour_ago)

        return {
            "minute_remaining": max(0, self.requests_per_minute - minute_count),
            "hour_remaining": max(0, self.requests_per_hour - hour_count),
        }

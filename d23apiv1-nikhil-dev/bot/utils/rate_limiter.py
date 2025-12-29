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

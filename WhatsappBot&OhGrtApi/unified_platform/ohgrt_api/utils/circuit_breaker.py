"""
Circuit breaker implementation for fault tolerance.

Provides automatic failure detection and graceful degradation for external services.
Implements the Circuit Breaker pattern to prevent cascading failures.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from ohgrt_api.logger import get_logger

logger = get_logger(component="circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation - requests pass through
    OPEN = "open"           # Circuit tripped - requests fail fast
    HALF_OPEN = "half_open" # Testing recovery - limited requests allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    # Number of failures before opening circuit
    failure_threshold: int = 5
    # Time in seconds before attempting recovery
    recovery_timeout: float = 30.0
    # Number of successful requests to close circuit
    success_threshold: int = 3
    # Exceptions that trigger the circuit breaker
    expected_exceptions: tuple = (Exception,)
    # Exceptions that should NOT trigger the circuit breaker
    excluded_exceptions: tuple = ()


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker."""
    failures: int = 0
    successes: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    state_changes: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, retry_after: float):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{circuit_name}' is open. "
            f"Retry after {retry_after:.1f} seconds."
        )


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker("weather_api")

        async def get_weather():
            async with breaker:
                return await weather_api.fetch()

        # Or as decorator:
        @breaker
        async def get_weather():
            return await weather_api.fetch()
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._half_open_requests = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def _should_allow_request(self) -> bool:
        """Determine if a request should be allowed."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self._stats.last_failure_time:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            return self._half_open_requests < self.config.success_threshold

        return False

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new circuit state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats.state_changes += 1

            if new_state == CircuitState.HALF_OPEN:
                self._half_open_requests = 0

            logger.info(
                "circuit_state_changed",
                circuit=self.name,
                old_state=old_state.value,
                new_state=new_state.value,
                consecutive_failures=self._stats.consecutive_failures,
            )

    def _record_success(self) -> None:
        """Record a successful request."""
        self._stats.successes += 1
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = time.time()
        self._stats.total_requests += 1

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_requests += 1
            if self._stats.consecutive_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def _record_failure(self, error: Exception) -> None:
        """Record a failed request."""
        self._stats.failures += 1
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0
        self._stats.last_failure_time = time.time()
        self._stats.total_requests += 1
        self._stats.total_failures += 1

        logger.warning(
            "circuit_failure_recorded",
            circuit=self.name,
            error=str(error),
            error_type=type(error).__name__,
            consecutive_failures=self._stats.consecutive_failures,
        )

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open returns to open
            self._transition_to(CircuitState.OPEN)
        elif (
            self._state == CircuitState.CLOSED
            and self._stats.consecutive_failures >= self.config.failure_threshold
        ):
            self._transition_to(CircuitState.OPEN)

    def _is_tracked_exception(self, error: Exception) -> bool:
        """Check if exception should trigger the circuit breaker."""
        if isinstance(error, self.config.excluded_exceptions):
            return False
        return isinstance(error, self.config.expected_exceptions)

    async def __aenter__(self):
        """Async context manager entry."""
        async with self._lock:
            if not self._should_allow_request():
                retry_after = 0.0
                if self._stats.last_failure_time:
                    elapsed = time.time() - self._stats.last_failure_time
                    retry_after = max(0, self.config.recovery_timeout - elapsed)
                raise CircuitBreakerError(self.name, retry_after)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        async with self._lock:
            if exc_val is None:
                self._record_success()
            elif self._is_tracked_exception(exc_val):
                self._record_failure(exc_val)
        return False  # Don't suppress exceptions

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap a function with circuit breaker."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)
        return wrapper

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_requests = 0
        logger.info("circuit_reset", circuit=self.name)


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """
    Get or create a named circuit breaker.

    Circuit breakers are reused by name to maintain state across calls.

    Args:
        name: Unique name for the circuit breaker
        config: Optional configuration (only used on creation)

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    for breaker in _circuit_breakers.values():
        breaker.reset()


# Pre-configured circuit breakers for common services
weather_circuit = get_circuit_breaker(
    "weather_api",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2,
    ),
)

llm_circuit = get_circuit_breaker(
    "llm_api",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=3,
    ),
)

github_circuit = get_circuit_breaker(
    "github_api",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=45.0,
        success_threshold=2,
    ),
)

database_circuit = get_circuit_breaker(
    "database",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=15.0,
        success_threshold=1,
    ),
)

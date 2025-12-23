"""
Prometheus metrics middleware and collectors.

Provides request/response metrics, business metrics, and a /metrics endpoint.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger import logger


class MetricsCollector:
    """
    Simple metrics collector that provides Prometheus-compatible output.

    Collects:
    - Request counts by endpoint and status
    - Request latency histograms
    - Active requests gauge
    - Business metrics (messages, users, etc.)
    """

    def __init__(self):
        self._lock = Lock()

        # Counters
        self._request_count: Dict[str, int] = defaultdict(int)
        self._request_errors: Dict[str, int] = defaultdict(int)

        # Histograms (simplified - stores all values)
        self._request_latency: Dict[str, List[float]] = defaultdict(list)

        # Gauges
        self._active_requests: int = 0

        # Business metrics
        self._messages_sent: int = 0
        self._messages_by_category: Dict[str, int] = defaultdict(int)
        self._active_users: int = 0
        self._auth_attempts: int = 0
        self._auth_failures: int = 0

        # Rate limit metrics
        self._rate_limit_hits: int = 0

        # Start time for uptime calculation
        self._start_time = time.time()

    # Request metrics
    def inc_request_count(self, method: str, path: str, status: int) -> None:
        """Increment request counter."""
        with self._lock:
            key = f"{method}:{path}:{status}"
            self._request_count[key] += 1

            if status >= 400:
                error_key = f"{method}:{path}"
                self._request_errors[error_key] += 1

    def observe_latency(self, method: str, path: str, latency: float) -> None:
        """Record request latency."""
        with self._lock:
            key = f"{method}:{path}"
            self._request_latency[key].append(latency)
            # Keep only last 1000 samples per endpoint
            if len(self._request_latency[key]) > 1000:
                self._request_latency[key] = self._request_latency[key][-1000:]

    def inc_active_requests(self) -> None:
        """Increment active requests gauge."""
        with self._lock:
            self._active_requests += 1

    def dec_active_requests(self) -> None:
        """Decrement active requests gauge."""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    # Business metrics
    def inc_messages_sent(self, category: str = "chat") -> None:
        """Increment messages sent counter."""
        with self._lock:
            self._messages_sent += 1
            self._messages_by_category[category] += 1

    def inc_auth_attempt(self, success: bool) -> None:
        """Record auth attempt."""
        with self._lock:
            self._auth_attempts += 1
            if not success:
                self._auth_failures += 1

    def inc_rate_limit_hit(self) -> None:
        """Increment rate limit hit counter."""
        with self._lock:
            self._rate_limit_hits += 1

    def set_active_users(self, count: int) -> None:
        """Set active users gauge."""
        with self._lock:
            self._active_users = count

    # Export metrics
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-compatible metrics string
        """
        lines = []
        now = int(time.time() * 1000)

        with self._lock:
            # Uptime
            uptime = time.time() - self._start_time
            lines.append("# HELP ohgrt_uptime_seconds Application uptime in seconds")
            lines.append("# TYPE ohgrt_uptime_seconds gauge")
            lines.append(f"ohgrt_uptime_seconds {uptime:.2f}")
            lines.append("")

            # Active requests
            lines.append("# HELP ohgrt_active_requests Number of active requests")
            lines.append("# TYPE ohgrt_active_requests gauge")
            lines.append(f"ohgrt_active_requests {self._active_requests}")
            lines.append("")

            # Request count
            lines.append("# HELP ohgrt_http_requests_total Total HTTP requests")
            lines.append("# TYPE ohgrt_http_requests_total counter")
            for key, count in self._request_count.items():
                method, path, status = key.split(":")
                # Normalize path for cardinality
                normalized_path = self._normalize_path(path)
                lines.append(
                    f'ohgrt_http_requests_total{{method="{method}",path="{normalized_path}",status="{status}"}} {count}'
                )
            lines.append("")

            # Request errors
            lines.append("# HELP ohgrt_http_errors_total Total HTTP errors")
            lines.append("# TYPE ohgrt_http_errors_total counter")
            for key, count in self._request_errors.items():
                method, path = key.split(":")
                normalized_path = self._normalize_path(path)
                lines.append(
                    f'ohgrt_http_errors_total{{method="{method}",path="{normalized_path}"}} {count}'
                )
            lines.append("")

            # Request latency (simplified percentiles)
            lines.append("# HELP ohgrt_http_request_duration_seconds Request latency")
            lines.append("# TYPE ohgrt_http_request_duration_seconds summary")
            for key, latencies in self._request_latency.items():
                if latencies:
                    method, path = key.split(":")
                    normalized_path = self._normalize_path(path)
                    sorted_latencies = sorted(latencies)
                    count = len(sorted_latencies)
                    total = sum(sorted_latencies)

                    # Calculate percentiles
                    p50 = sorted_latencies[int(count * 0.5)] if count > 0 else 0
                    p90 = sorted_latencies[int(count * 0.9)] if count > 0 else 0
                    p99 = sorted_latencies[int(count * 0.99)] if count > 0 else 0

                    base = f'ohgrt_http_request_duration_seconds{{method="{method}",path="{normalized_path}"'
                    lines.append(f'{base},quantile="0.5"}} {p50:.4f}')
                    lines.append(f'{base},quantile="0.9"}} {p90:.4f}')
                    lines.append(f'{base},quantile="0.99"}} {p99:.4f}')
                    lines.append(f'{base[:-1]}_sum}} {total:.4f}')
                    lines.append(f'{base[:-1]}_count}} {count}')
            lines.append("")

            # Messages
            lines.append("# HELP ohgrt_messages_total Total messages sent")
            lines.append("# TYPE ohgrt_messages_total counter")
            lines.append(f"ohgrt_messages_total {self._messages_sent}")
            for category, count in self._messages_by_category.items():
                lines.append(f'ohgrt_messages_total{{category="{category}"}} {count}')
            lines.append("")

            # Auth metrics
            lines.append("# HELP ohgrt_auth_attempts_total Total auth attempts")
            lines.append("# TYPE ohgrt_auth_attempts_total counter")
            lines.append(f"ohgrt_auth_attempts_total {self._auth_attempts}")
            lines.append(f'ohgrt_auth_attempts_total{{result="failure"}} {self._auth_failures}')
            lines.append("")

            # Rate limiting
            lines.append("# HELP ohgrt_rate_limit_hits_total Total rate limit hits")
            lines.append("# TYPE ohgrt_rate_limit_hits_total counter")
            lines.append(f"ohgrt_rate_limit_hits_total {self._rate_limit_hits}")
            lines.append("")

            # Active users
            lines.append("# HELP ohgrt_active_users Number of active users")
            lines.append("# TYPE ohgrt_active_users gauge")
            lines.append(f"ohgrt_active_users {self._active_users}")

        return "\n".join(lines)

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to reduce cardinality.

        Replaces UUIDs and IDs with placeholders.
        """
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            ":id",
            path,
            flags=re.IGNORECASE,
        )
        # Replace numeric IDs
        path = re.sub(r"/\d+", "/:id", path)
        return path


# Global metrics collector
metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics.

    Records:
    - Request count by method, path, and status
    - Request latency
    - Active request count
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        # Track active requests
        metrics.inc_active_requests()
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            status = 500
            raise
        finally:
            # Record metrics
            latency = time.time() - start_time
            metrics.dec_active_requests()
            metrics.inc_request_count(method, path, status)
            metrics.observe_latency(method, path, latency)

            # Log slow requests
            if latency > 1.0:
                logger.warning(
                    "slow_request",
                    method=method,
                    path=path,
                    latency_seconds=round(latency, 3),
                )

        return response

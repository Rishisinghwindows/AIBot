"""
Metrics Middleware.

Collects request metrics for monitoring.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    """Metrics collection class."""

    request_count: int = 0
    request_duration_total: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    endpoints: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_request(
        self,
        path: str,
        status_code: int,
        duration: float,
    ) -> None:
        """Record a request."""
        self.request_count += 1
        self.request_duration_total += duration
        self.status_codes[status_code] += 1
        self.endpoints[path] += 1

    @property
    def average_duration(self) -> float:
        """Average request duration."""
        if self.request_count == 0:
            return 0.0
        return self.request_duration_total / self.request_count

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = [
            f"# HELP http_requests_total Total HTTP requests",
            f"# TYPE http_requests_total counter",
            f"http_requests_total {self.request_count}",
            f"",
            f"# HELP http_request_duration_seconds_total Total HTTP request duration",
            f"# TYPE http_request_duration_seconds_total counter",
            f"http_request_duration_seconds_total {self.request_duration_total}",
            f"",
            f"# HELP http_requests_by_status HTTP requests by status code",
            f"# TYPE http_requests_by_status counter",
        ]

        for code, count in self.status_codes.items():
            lines.append(f'http_requests_by_status{{status_code="{code}"}} {count}')

        return "\n".join(lines)


# Global metrics instance
metrics = Metrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        metrics.record_request(
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"

        return response

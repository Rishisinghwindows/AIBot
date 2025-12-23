"""
Web Chat Module

Provides anonymous chat functionality for D23Web landing page.
No authentication required - uses session-based tracking.
"""

from app.web.router import router as web_router

__all__ = ["web_router"]

"""
Common module - Shared code between WhatsApp Bot and OhGrt API.

This module contains:
- Base configuration classes
- Shared models
- LLM client utilities
- Common services (weather, news, astrology)
- WhatsApp client
- Database utilities
- Internationalization
- Utility functions
"""

from common.config.settings import Settings, get_settings, get_base_settings, settings

__version__ = "1.0.0"

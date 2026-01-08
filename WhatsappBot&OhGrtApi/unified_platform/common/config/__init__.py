"""
Configuration management for the unified platform.

Provides base configuration classes that can be extended by
whatsapp_bot and ohgrt_api modules.
"""

from common.config.settings import Settings, get_settings, get_base_settings, settings

__all__ = ["Settings", "get_settings", "get_base_settings", "settings"]

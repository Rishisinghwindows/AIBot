"""
WhatsApp Cloud API Integration

Handles webhook processing and message sending via Meta Cloud API.
"""

from bot.whatsapp.client import WhatsAppClient, get_whatsapp_client
from bot.whatsapp.webhook import router as whatsapp_router
from bot.whatsapp.models import WebhookPayload, extract_message

__all__ = [
    "WhatsAppClient",
    "get_whatsapp_client",
    "whatsapp_router",
    "WebhookPayload",
    "extract_message",
]

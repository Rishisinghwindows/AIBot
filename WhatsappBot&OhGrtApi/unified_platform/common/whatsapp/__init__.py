"""
WhatsApp Cloud API Integration

Handles webhook processing and message sending via Meta Cloud API.
"""

from common.whatsapp.client import WhatsAppClient, get_whatsapp_client
from common.whatsapp.webhook import router as whatsapp_router
from common.whatsapp.models import WebhookPayload, extract_message

__all__ = [
    "WhatsAppClient",
    "get_whatsapp_client",
    "whatsapp_router",
    "WebhookPayload",
    "extract_message",
]

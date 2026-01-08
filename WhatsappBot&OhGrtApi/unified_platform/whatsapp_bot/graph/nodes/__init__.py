"""
WhatsApp Bot specific graph nodes.
"""

from whatsapp_bot.graph.nodes.pnr_status import handle_pnr_status
from whatsapp_bot.graph.nodes.train_status import handle_train_status
from whatsapp_bot.graph.nodes.subscription import handle_subscription
from whatsapp_bot.graph.nodes.astro import handle_horoscope
from whatsapp_bot.graph.nodes.image import handle_image_generation
from whatsapp_bot.graph.nodes.reminder import handle_reminder
from whatsapp_bot.graph.nodes.help import handle_help

__all__ = [
    "handle_pnr_status",
    "handle_train_status",
    "handle_subscription",
    "handle_horoscope",
    "handle_image_generation",
    "handle_reminder",
    "handle_help",
]

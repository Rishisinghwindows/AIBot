"""
WhatsApp Integration Module

Handles WhatsApp Cloud API webhook and message sending.
"""

from app.whatsapp.router import router as whatsapp_router

__all__ = ["whatsapp_router"]

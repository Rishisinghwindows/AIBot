"""
WhatsApp Bot - FastAPI Application Entry Point.

This is the main entry point for the WhatsApp Bot application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from whatsapp_bot.config import settings
from whatsapp_bot.webhook import router as whatsapp_router
from whatsapp_bot.services.reminder_service import get_reminder_service
from common.whatsapp.client import initialize_whatsapp_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting WhatsApp Bot services...")

    # Initialize WhatsApp client
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        initialize_whatsapp_client(
            access_token=settings.whatsapp_access_token,
            phone_number_id=settings.whatsapp_phone_number_id,
        )
        logger.info("WhatsApp client initialized")

    # Start reminder scheduler
    reminder_service = get_reminder_service()
    reminder_service.start_scheduler()
    logger.info("Reminder scheduler started")

    # Configure LangSmith if enabled
    settings.configure_langsmith()

    yield

    # Shutdown
    logger.info("Shutting down WhatsApp Bot services...")
    reminder_service.stop_scheduler()


app = FastAPI(
    lifespan=lifespan,
    title=settings.bot_name,
    version=settings.bot_version,
    description="WhatsApp AI Assistant Bot",
)


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.bot_name,
        "version": settings.bot_version,
        "features": [
            "Daily Horoscope Subscription",
            "Transit Alerts",
            "PNR Status",
            "Weather",
            "News",
            "Image Generation",
            "Reminders",
        ],
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "lite_mode": settings.lite_mode,
        "environment": settings.environment,
    }


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    """Privacy Policy page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - D23 AI</title>
    <style>
        body { font-family: system-ui; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #667eea; }
        h2 { color: #764ba2; }
    </style>
</head>
<body>
    <h1>Privacy Policy</h1>
    <p>Your privacy is important to us. This WhatsApp bot collects minimal data necessary to provide services.</p>
    <h2>Data We Collect</h2>
    <ul>
        <li>Phone number (for communication)</li>
        <li>Messages you send to the bot</li>
        <li>Subscription preferences</li>
    </ul>
    <h2>How We Use Data</h2>
    <ul>
        <li>To provide bot services</li>
        <li>To send subscribed content</li>
        <li>To improve our services</li>
    </ul>
    <h2>Contact</h2>
    <p>For questions, send a message to the bot or email privacy@d23ai.in</p>
</body>
</html>
"""


# Include routers
app.include_router(whatsapp_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002)

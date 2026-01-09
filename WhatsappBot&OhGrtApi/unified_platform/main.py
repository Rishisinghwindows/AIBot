"""
Unified Platform - Combined OhGrt API + D23 WhatsApp Bot

This unified main.py runs both the OhGrt API and WhatsApp Bot on a single port.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
import uvicorn

# Import configurations
from common.config.settings import get_base_settings
from ohgrt_api.config import settings as api_settings

# Import routers
from ohgrt_api.auth import router as auth_router
from ohgrt_api.chat import router as chat_router
from whatsapp_bot.webhook.handler import router as whatsapp_router
from whatsapp_bot.test_interface import router as test_router

# Import new OhGrt routers (with fallback for optional dependencies)
try:
    from ohgrt_api.mcp.router import router as mcp_router
    MCP_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP router not available: {e}")
    MCP_AVAILABLE = False
    mcp_router = None

try:
    from ohgrt_api.personas.router import router as personas_router
    PERSONAS_AVAILABLE = True
except ImportError as e:
    PERSONAS_AVAILABLE = False
    personas_router = None

try:
    from ohgrt_api.tasks.router import router as tasks_router
    TASKS_AVAILABLE = True
except ImportError as e:
    TASKS_AVAILABLE = False
    tasks_router = None

try:
    from ohgrt_api.web.router import router as web_router
    WEB_AVAILABLE = True
except ImportError as e:
    WEB_AVAILABLE = False
    web_router = None

try:
    from ohgrt_api.graph.router import router as graph_router
    GRAPH_AVAILABLE = True
except ImportError as e:
    GRAPH_AVAILABLE = False
    graph_router = None

# Import middleware (with fallback for compatibility)
try:
    from ohgrt_api.middleware import (
        SecurityHeadersMiddleware,
        RateLimitMiddleware,
        MetricsMiddleware,
    )
    from ohgrt_api.middleware.metrics import metrics
    MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Middleware import failed, running without middleware: {e}")
    MIDDLEWARE_AVAILABLE = False
    metrics = None

# Import services
from common.whatsapp.client import initialize_whatsapp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get base settings
base_settings = get_base_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Unified Platform services...")

    # Store settings in app state
    app.state.settings = api_settings

    # Initialize WhatsApp client if configured
    if base_settings.WHATSAPP_ACCESS_TOKEN and base_settings.WHATSAPP_PHONE_NUMBER_ID:
        initialize_whatsapp_client(
            access_token=base_settings.WHATSAPP_ACCESS_TOKEN,
            phone_number_id=base_settings.WHATSAPP_PHONE_NUMBER_ID,
        )
        logger.info("WhatsApp client initialized")

    # Start bot services if not in lite mode
    if not base_settings.LITE_MODE:
        try:
            from common.services.reminder_service import ReminderService
            ReminderService.start_scheduler()
            logger.info("Reminder scheduler started")
        except Exception as e:
            logger.warning(f"Could not start reminder service: {e}")

        try:
            from common.services.horoscope_scheduler import start_horoscope_scheduler
            from common.services.transit_service import start_transit_service
            await start_horoscope_scheduler()
            await start_transit_service()
            logger.info("Horoscope and Transit services started")
        except Exception as e:
            logger.warning(f"Could not start subscription services: {e}")
    else:
        logger.info("Running in LITE_MODE - background services disabled")

    # Configure LangSmith if available
    try:
        api_settings.configure_langsmith()
    except Exception as e:
        logger.debug(f"LangSmith configuration skipped: {e}")

    logger.info(f"Unified Platform v2.1.0 started on port 9002")

    yield

    # Shutdown
    logger.info("Shutting down Unified Platform services...")

    if not base_settings.LITE_MODE:
        try:
            from common.services.reminder_service import ReminderService
            ReminderService.shutdown_scheduler()
        except Exception:
            pass

        try:
            from common.services.horoscope_scheduler import stop_horoscope_scheduler
            from common.services.transit_service import stop_transit_service
            await stop_horoscope_scheduler()
            await stop_transit_service()
        except Exception:
            pass


app = FastAPI(
    lifespan=lifespan,
    title="Unified Platform - OhGrt API + D23Bot",
    description="""
# Unified AI Platform

A combined platform providing:

## OhGrt API Features
- **Google Authentication**: Sign in with Google via Firebase
- **AI Chat**: Intelligent chat with tool-use capabilities
- **Provider Integrations**: Connect GitHub, Jira, Slack, and more
- **RAG Support**: Upload and query PDF documents

## D23 WhatsApp Bot Features
- **Vedic Astrology**: Horoscopes, birth charts, kundli matching
- **Daily Subscriptions**: Automated horoscope delivery
- **Transit Alerts**: Planetary movement notifications
- **Utility Services**: Weather, news, train status, and more
- **22 Indian Languages**: Multi-language support
    """,
    version="2.1.0",
    contact={
        "name": "Support",
        "email": "support@d23ai.in",
    },
)


# Exception handlers
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception(
        "unhandled_exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
        },
    )


# Middleware (order: last added = first executed)
if MIDDLEWARE_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MetricsMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Include routers
app.include_router(auth_router)  # /auth/*
app.include_router(chat_router)  # /chat/*
app.include_router(whatsapp_router)  # /whatsapp/webhook
app.include_router(test_router)  # /test/* - Test interface

# Include new OhGrt routers (if available)
if MCP_AVAILABLE and mcp_router:
    app.include_router(mcp_router)  # /mcp/*

if PERSONAS_AVAILABLE and personas_router:
    app.include_router(personas_router)  # /personas/*

if TASKS_AVAILABLE and tasks_router:
    app.include_router(tasks_router)  # /tasks/*

if WEB_AVAILABLE and web_router:
    app.include_router(web_router)  # /web/*

if GRAPH_AVAILABLE and graph_router:
    app.include_router(graph_router)  # /graph/*


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Unified Platform",
        "version": "2.1.0",
        "status": "healthy",
        "components": {
            "ohgrt_api": "active",
            "whatsapp_bot": "active",
        },
        "features": [
            "AI Chat with Tools",
            "Google Authentication",
            "Vedic Astrology",
            "Daily Horoscope Subscriptions",
            "Transit Alerts",
            "22 Indian Languages",
            "Weather & News",
            "Train PNR Status",
        ]
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "lite_mode": base_settings.LITE_MODE,
        "environment": base_settings.ENVIRONMENT,
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"status": "ready"}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    if metrics:
        return PlainTextResponse(
            content=metrics.export_prometheus(),
            media_type="text/plain; charset=utf-8",
        )
    return PlainTextResponse(content="# Metrics not available", media_type="text/plain")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    """Privacy Policy page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - D23 AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        h2 { color: #667eea; margin: 30px 0 15px 0; }
        p { margin: 12px 0; color: #555; }
        ul { margin: 15px 0 15px 25px; color: #555; }
        li { margin: 8px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Privacy Policy</h1>
        <p><strong>Effective Date:</strong> December 26, 2025</p>
        <p>D23 AI respects your privacy. We collect only necessary information to provide our services.</p>
        <h2>Information We Collect</h2>
        <ul>
            <li>Phone number for WhatsApp communication</li>
            <li>Messages you send to our bot</li>
            <li>Birth details for astrology services (if provided)</li>
        </ul>
        <h2>Contact</h2>
        <p>Email: <a href="mailto:privacy@d23ai.in">privacy@d23ai.in</a></p>
    </div>
</body>
</html>
"""


@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    """Terms of Service page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - D23 AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
        }
        h1 { color: #667eea; margin-bottom: 20px; }
        h2 { color: #667eea; margin: 30px 0 15px 0; }
        p { margin: 12px 0; color: #555; }
        ul { margin: 15px 0 15px 25px; color: #555; }
        li { margin: 8px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terms of Service</h1>
        <p><strong>Effective Date:</strong> December 26, 2025</p>
        <p>By using D23 AI, you agree to these Terms of Service.</p>
        <h2>Service Description</h2>
        <p>D23 AI provides AI-powered assistance including astrology readings, utility services, and general chat.</p>
        <h2>Disclaimer</h2>
        <p>Astrological readings are for entertainment purposes only and should not substitute professional advice.</p>
        <h2>Contact</h2>
        <p>Email: <a href="mailto:support@d23ai.in">support@d23ai.in</a></p>
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9002,
        reload=True,
        log_level="info",
    )

from __future__ import annotations

import re
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Ensure project root is on sys.path for imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.auth import auth_router
from app.chat import chat_router
from app.whatsapp import whatsapp_router
from app.web import web_router
from app.tasks.router import router as tasks_router, web_router as tasks_web_router
from app.oauth import gmail_router, github_router, slack_router, jira_router, uber_router
from app.personas.router import router as personas_router, public_router as personas_public_router
from app.mcp.router import router as mcp_router
from app.tasks.scheduler import start_scheduler, stop_scheduler
from app.services.email_scheduler import start_email_scheduler, stop_email_scheduler
from app.config import Settings, get_settings
from app.db.base import Base, engine, SessionLocal
from app.exceptions import OhGrtException, RateLimitExceededError, ServiceUnavailableError
from app.graph.tool_agent import build_tool_agent
from app.logger import configure_logging, logger
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.metrics import MetricsMiddleware, metrics
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.utils.models import AskRequest, AskResponse, PDFIngestResponse, WeatherResponse

app = FastAPI(
    title="OhGrt API",
    description="""
# OhGrt Agentic AI API

An intelligent AI assistant API with tool-use capabilities and multi-provider integrations.

## Features

- **Google Authentication**: Sign in with Google via Firebase
- **AI Chat**: Intelligent chat with tool-use capabilities
- **Provider Integrations**: Connect GitHub, Jira, Slack, and more
- **RAG Support**: Upload and query PDF documents
- **Weather Queries**: Get real-time weather information

## Authentication

All protected endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Additionally, all requests (except exempt paths) require security headers:
- `X-Request-ID`: Unique request identifier (UUID)
- `X-Nonce`: One-time value for replay protection
- `X-Timestamp`: Unix timestamp (must be within 5 minutes of server time)

## Rate Limiting

Requests are rate-limited per user/IP:
- Default: 100 requests per minute
- Auth endpoints: 10 requests per minute

Rate limit headers in responses:
- `X-RateLimit-Limit`: Max requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Reset timestamp
    """,
    version="2.1.0",
    contact={
        "name": "OhGrt Support",
        "email": "support@ohgrt.com",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and provider connection endpoints",
        },
        {
            "name": "chat",
            "description": "AI chat messaging and conversation management",
        },
        {
            "name": "health",
            "description": "Health check and metrics endpoints",
        },
    ],
)


# Exception handlers for custom exceptions
@app.exception_handler(OhGrtException)
async def ohgrt_exception_handler(request: Request, exc: OhGrtException):
    """Handle all custom OhGrt exceptions."""
    logger.warning(
        "ohgrt_exception",
        error_code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
    # Add retry-after header for rate limit and service unavailable errors
    if isinstance(exc, RateLimitExceededError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)
    elif isinstance(exc, ServiceUnavailableError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors with user-friendly messages."""
    errors = exc.errors()
    # Extract field-level errors for clearer messages
    field_errors = []
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(l) for l in loc if l != "body")
        msg = error.get("msg", "Invalid value")
        field_errors.append({"field": field, "message": msg})

    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=field_errors,
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": {"errors": field_errors},
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions with consistent format."""
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": str(exc.detail) if exc.detail else "An error occurred",
            "details": {"status_code": exc.status_code},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions to prevent information leakage."""
    # Log the full error for debugging
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    # Return a generic error to the client (don't expose internal details)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {},
        },
    )


# Get settings for CORS configuration
_settings = get_settings()

# Middleware order: Last added = First executed on requests
# So we add in reverse order of desired execution

# Security headers middleware (validates X-Request-ID, X-Nonce, X-Timestamp)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Metrics middleware (captures request metrics)
app.add_middleware(MetricsMiddleware)

# Correlation ID middleware (sets up request context for logging)
app.add_middleware(CorrelationIdMiddleware)

# CORS middleware - MUST be added last so it's executed first
# This ensures CORS preflight (OPTIONS) requests are handled before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(whatsapp_router)
app.include_router(web_router)
app.include_router(tasks_router)
app.include_router(tasks_web_router)

# OAuth routers
app.include_router(gmail_router)
app.include_router(github_router)
app.include_router(slack_router)
app.include_router(jira_router)
app.include_router(uber_router)

# Persona routers
app.include_router(personas_router)
app.include_router(personas_public_router)

# MCP router
app.include_router(mcp_router)


def get_services(settings: Settings):
    rag_service = RAGService(settings)
    weather_service = WeatherService(settings)
    return {"rag": rag_service, "weather": weather_service}


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    # Create database tables (optional - skip if DB not available)
    if engine is not None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("database_tables_created")
            app.state.db_available = True
        except Exception as e:
            logger.warning("database_connection_failed", error=str(e))
            logger.info("running_without_database", message="Some features may be limited")
            app.state.db_available = False
    else:
        logger.info("running_without_database", message="Database not configured")
        app.state.db_available = False

    app.state.settings = settings
    app.state.agent = build_tool_agent(settings)
    app.state.services = get_services(settings)

    # Start the task scheduler
    await start_scheduler()

    # Start the email scheduler
    try:
        start_email_scheduler()
        logger.info("email_scheduler_started")
    except Exception as e:
        logger.warning("email_scheduler_start_failed", error=str(e))

    # Start MCP health checks (background monitoring)
    try:
        from app.mcp.manager import MCPManager
        mcp_manager = MCPManager.get_instance()
        await mcp_manager.start_health_checks()
        logger.info("mcp_health_checks_started")
    except Exception as e:
        logger.warning("mcp_health_checks_failed", error=str(e))

    logger.info("app_startup", version="2.1.0")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown handler - stop background services."""
    await stop_scheduler()

    # Stop email scheduler
    try:
        stop_email_scheduler()
        logger.info("email_scheduler_stopped")
    except Exception as e:
        logger.warning("email_scheduler_stop_failed", error=str(e))

    # Stop MCP health checks
    try:
        from app.mcp.manager import MCPManager
        mcp_manager = MCPManager.get_instance()
        await mcp_manager.stop_health_checks()
        logger.info("mcp_health_checks_stopped")
    except Exception as e:
        logger.warning("mcp_health_checks_stop_failed", error=str(e))

    logger.info("app_shutdown")


def get_agent():
    agent = getattr(app.state, "agent", None)
    if not agent:
        settings = get_settings()
        app.state.agent = build_tool_agent(settings)
    return app.state.agent


def get_rag_service():
    services = getattr(app.state, "services", {}) or get_services(get_settings())
    return services["rag"]


def get_weather_service():
    services = getattr(app.state, "services", {}) or get_services(get_settings())
    return services["weather"]


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": "2.1.0"}


@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe.

    Returns 200 if the service is running.
    Used to detect if the container needs to be restarted.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe.

    Returns 200 if the service is ready to accept traffic.
    Checks database connectivity.
    """
    checks = {
        "database": False,
        "status": "not_ready",
    }

    # Check database connection
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.warning("readiness_check_db_failed", error=str(e))
        checks["database"] = False
        checks["database_error"] = str(e)

    # Determine overall status
    if checks["database"]:
        checks["status"] = "ready"
        return checks
    else:
        return JSONResponse(status_code=503, content=checks)


@app.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    """
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        content=metrics.export_prometheus(),
        media_type="text/plain; charset=utf-8",
    )


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, agent=Depends(get_agent)):
    """
    Send a message to the AI agent (legacy endpoint).

    For authenticated chat with history, use /chat/send instead.
    """
    result = await agent.invoke(request.message)
    if "response" not in result:
        raise HTTPException(status_code=500, detail="Agent failed to respond")

    return AskResponse(
        category=result.get("category", "chat"),
        response=result["response"],
        route_log=result.get("route_log", []),
        metadata=result.get("metadata", {}),
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other security issues.

    - Removes path components (directories)
    - Removes null bytes and other dangerous characters
    - Ensures filename ends with .pdf
    - Generates unique filename with original name prefix
    """
    if not filename:
        return f"{uuid.uuid4().hex}.pdf"

    # Get only the base filename (remove any path components)
    base_name = Path(filename).name

    # Remove null bytes and other dangerous characters
    base_name = base_name.replace("\x00", "")

    # Remove any remaining path separators that might have been encoded
    base_name = re.sub(r'[/\\]', '', base_name)

    # Remove leading dots to prevent hidden files
    base_name = base_name.lstrip('.')

    # Keep only alphanumeric, dash, underscore, and dot
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name)

    # Ensure it's not empty after sanitization
    if not safe_name or safe_name == '.pdf':
        safe_name = "document"

    # Remove .pdf extension if present (we'll add it back)
    if safe_name.lower().endswith('.pdf'):
        safe_name = safe_name[:-4]

    # Truncate if too long (max 100 chars for the base name)
    if len(safe_name) > 100:
        safe_name = safe_name[:100]

    # Add unique suffix to prevent collisions and ensure .pdf extension
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{safe_name}_{unique_suffix}.pdf"


@app.post("/pdf/upload", response_model=PDFIngestResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    rag_service: RAGService = Depends(get_rag_service),
):
    """Upload and ingest a PDF file for RAG queries."""
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed.")
    try:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
    except Exception:  # noqa: BLE001
        size = 0
    if size and size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large (max 10MB).")

    # Sanitize filename to prevent path traversal attacks
    safe_filename = sanitize_filename(file.filename)

    pdf_dir = Path(__file__).resolve().parent.parent / "data" / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    dest = pdf_dir / safe_filename

    # Double-check the destination is within the pdf_dir (defense in depth)
    try:
        dest.resolve().relative_to(pdf_dir.resolve())
    except ValueError:
        logger.warning("pdf_upload_path_traversal_attempt", original=file.filename)
        raise HTTPException(status_code=400, detail="Invalid filename.")

    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks, table = await rag_service.ingest_pdf(dest)
    logger.info("pdf_uploaded", file=str(dest), chunks=chunks, original_name=file.filename)
    return PDFIngestResponse(
        filename=safe_filename, chunks=chunks, status="ingested", vector_table=table
    )


@app.get("/weather", response_model=WeatherResponse)
async def weather(
    city: str,
    service: WeatherService = Depends(get_weather_service),
):
    """Get current weather for a city."""
    return await service.get_weather(city)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=9002, reload=True)

"""
PALA Backend — Main Application Entry Point
Personal AI Life Analyzer — FastAPI server.

Assembles all routers, middleware, and startup events.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.middleware.rate_limiter import limiter
from app.routers import auth, usage, steps, expenses, insights, query
from app.schemas.common import error_response, success_response

# ── Import all models so Base.metadata knows about them ───────
from app.models import User, UsageLog, Step, Expense  # noqa: F401
from app.models.query_history import QueryHistory  # noqa: F401  (registers query_history table)

settings = get_settings()


# ── Structured JSON Logging (NFR-B5) ─────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pala")


# ── Lifespan — Create Tables on Startup ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (dev convenience)."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    yield
    logger.info("PALA backend shutting down.")


# ── FastAPI Application ──────────────────────────────────────
app = FastAPI(
    title="PALA — Personal AI Life Analyzer",
    description=(
        "Privacy-first self-tracking API. Collects screen time, step counts, "
        "and expenses, then applies RAG-based AI to surface actionable insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── Rate Limiter ─────────────────────────────────────────────
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return rate limit errors in the standard response envelope."""
    logger.warning(f"Rate limit exceeded on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response("Rate limit exceeded"),
    )

app.add_middleware(SlowAPIMiddleware)

# ── CORS Middleware (permissive for dev) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ─────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return HTTP errors in the standard response envelope."""
    logger.warning(f"HTTP error on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation errors in the standard response envelope."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response("Validation error", data=exc.errors()),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return consistent envelope."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response("Internal server error"),
    )


# ── Include Routers ──────────────────────────────────────────
app.include_router(auth.router)
app.include_router(usage.router)
app.include_router(steps.router)
app.include_router(expenses.router)
app.include_router(insights.router)
app.include_router(query.router)


# ── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    """Basic health check endpoint."""
    return success_response(data={"status": "healthy", "service": "PALA Backend", "version": "1.0.0"})

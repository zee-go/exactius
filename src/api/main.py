"""
FastAPI application entry point.

Main application for Exactius multi-account Meta ads automation platform.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.api.routes import accounts, campaigns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Exactius API server")
    logger.info("Initializing Secret Manager connection")

    yield

    # Shutdown
    logger.info("Shutting down Exactius API server")


# Create FastAPI application
app = FastAPI(
    title="Exactius API",
    description="Multi-account Meta ads automation platform for agencies",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default dev port
        "http://localhost:8000",  # FastAPI dev port
        "https://exactius.app",   # Production domain (if applicable)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "exactius-api",
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API welcome message
    """
    return {
        "message": "Exactius API - Multi-account Meta ads automation",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(accounts.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

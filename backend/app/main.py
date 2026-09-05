from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import dispose_database_engine
from app.core.exceptions import DealFlowException, dealflow_exception_handler, generic_exception_handler
from app.api.v1.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle event handler."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} backend in '{settings.APP_ENV}' environment...")
    logger.info(f"API v1 prefix mounted at: {settings.API_V1_STR}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME} backend gracefully...")
    await dispose_database_engine()


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="An Intelligent, Self-Governing Sales Operations Platform",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # Configure CORS Middleware
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    # Configure Trusted Host Middleware
    if settings.ALLOWED_HOSTS and settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )

    # Register Exception Handlers
    app.add_exception_handler(DealFlowException, dealflow_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Mount API v1 Router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

"""
FastAPI application — REST API for the Research Assistant.
Provides endpoints for research queries, report retrieval, and health checks.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.utils.config import settings
from src.utils.logger import setup_logger
from models.database import init_database, close_database

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Starting Research Assistant API...")

    # Initialize PostgreSQL
    try:
        await init_database(settings.database_url)
        logger.info("PostgreSQL database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize MinIO buckets
    try:
        from src.storage.minio_client import MinIOClient
        minio = MinIOClient()
        minio.ensure_buckets()
        logger.info("MinIO buckets ready")
    except Exception as e:
        logger.warning(f"MinIO initialization skipped: {e}")

    logger.info(f"API ready on {settings.api_host}:{settings.api_port}")
    yield

    # Shutdown
    logger.info("Shutting down Research Assistant API...")
    await close_database()


app = FastAPI(
    title="AI Research Assistant",
    description="Multi-agent research assistant that fetches, analyzes, and synthesizes academic papers into structured reports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck and monitoring."""
    return {
        "status": "healthy",
        "service": "research-assistant",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
        "model": settings.litellm_model,
    }

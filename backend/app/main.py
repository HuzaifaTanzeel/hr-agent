"""
FastAPI Main Application
"""
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.api.routes import router
from app.api.agent_routes import router as agent_router
from app.db.session import engine
from app.db.models.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)

# Get logger for this module
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown
    """
    # Startup
    logger.info("="*60)
    logger.info("🚀 Starting HR AI Agent API...")
    logger.info(f"   Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"   Debug Mode: {settings.DEBUG}")
    logger.info("="*60)
    
    # Note: Don't auto-create tables in production
    # Use Alembic migrations instead
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    logger.info("="*60)
    logger.info("🛑 Shutting down...")
    logger.info("="*60)
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="REST API for HR Leave Management System",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(
    router,
    prefix=settings.API_V1_PREFIX,
    tags=["Leave Management"]
)

# Include agent routes
app.include_router(
    agent_router,
    prefix=f"{settings.API_V1_PREFIX}/agent",
    tags=["HR Agent"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HR AI Agent API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
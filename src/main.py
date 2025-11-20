"""Main FastAPI application for AICompany Social Media Integration"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config import settings
from src.api.routes import twitter, instagram, tiktok
from src.models.schemas import HealthResponse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Automated social media posting integration for Twitter, Instagram, and TikTok",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred"
        }
    )


# Root endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


# API info endpoint
@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "platforms": ["twitter", "instagram", "tiktok"],
        "endpoints": {
            "twitter": {
                "post": "/api/v1/twitter/post",
                "thread": "/api/v1/twitter/thread",
                "delete": "/api/v1/twitter/{post_id}",
                "get": "/api/v1/twitter/{post_id}",
                "health": "/api/v1/twitter/health/status"
            },
            "instagram": {
                "post": "/api/v1/instagram/post",
                "story": "/api/v1/instagram/story",
                "reel": "/api/v1/instagram/reel",
                "delete": "/api/v1/instagram/{post_id}",
                "get": "/api/v1/instagram/{post_id}",
                "user_info": "/api/v1/instagram/user/info",
                "health": "/api/v1/instagram/health/status"
            },
            "tiktok": {
                "post": "/api/v1/tiktok/post",
                "delete": "/api/v1/tiktok/{post_id}",
                "get": "/api/v1/tiktok/{post_id}",
                "user_info": "/api/v1/tiktok/user/info",
                "health": "/api/v1/tiktok/health/status"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# Include routers
app.include_router(twitter.router, prefix="/api/v1")
app.include_router(instagram.router, prefix="/api/v1")
app.include_router(tiktok.router, prefix="/api/v1")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("API Documentation available at /docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )

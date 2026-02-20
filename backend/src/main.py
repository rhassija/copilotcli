"""FastAPI application entry point for Copilot CLI Web UI backend.

This module initializes the FastAPI application with all necessary middleware,
route handlers, and configuration for handling GitHub authentication, repository
management, and WebSocket operations.

Environment:
- GITHUB_TOKEN: GitHub personal access token (provided by client)
- DEBUG: Debug mode flag (default: False)
- HOST: Server host (default: 0.0.0.0)
- PORT: Server port (default: 8000)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from src.api import auth, websocket, repositories, documents, system
from src.utils.error_handlers import register_exception_handlers
from src.utils.logging import setup_logging

# Configure logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Copilot CLI Web UI Backend",
    description="Backend API for Copilot CLI web interface with GitHub integration and WebSocket support",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS middleware for frontend development
# Phase 1: Allow localhost development
# Phase 2: Restrict to specific origin
ALLOWED_ORIGINS = [
    "http://localhost:3000",    # Next.js dev server
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost:8000",     # Backend (for swagger docs)
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if not os.getenv("DEBUG") else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)

# Register exception handlers
register_exception_handlers(app)

# Register API routers
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(repositories.router)
app.include_router(documents.router)
app.include_router(system.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Copilot CLI Web UI Backend API",
        "docs": "/docs",
        "version": "0.1.0"
    }

# On startup
@app.on_event("startup")
async def startup_event():
    logger.info("Backend application starting up...")
    # TODO: Initialize GitHub client
    # TODO: Initialize WebSocket message queue

# On shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend application shutting down...")
    # TODO: Cleanup connections

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

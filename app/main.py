"""
Agentic Honeypot API - Main Application
A production-ready API that detects scam messages and autonomously engages scammers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.routers import scam_detection
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🍯 Agentic Honeypot API starting up...")
    logger.info(f"Callback URL: {settings.callback_url}")
    logger.info(f"Scam threshold: {settings.scam_threshold}")
    yield
    logger.info("🍯 Agentic Honeypot API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Agentic Honeypot API",
    description="""
    A production-ready API that detects scam messages and autonomously engages 
    scammers to extract intelligence.
    
    ## Features
    - 🔍 **Scam Detection**: Analyzes messages for scam patterns
    - 🤖 **AI Agent**: Human-like responses using Claude AI
    - 📊 **Intelligence Extraction**: Extracts bank accounts, UPI IDs, phone numbers, URLs
    - 📝 **Session Management**: Tracks conversations per session
    - 📡 **Automatic Callback**: Posts results to hackathon API when sufficient engagement
    
    ## Authentication
    All endpoints require an API key via the `x-api-key` header.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.log_level == "DEBUG" else None
        }
    )


# Include routers
app.include_router(scam_detection.router)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the API.
    """
    return {
        "status": "healthy",
        "service": "Agentic Honeypot API",
        "version": "1.0.0"
    }


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "🍯 Welcome to the Agentic Honeypot API",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "scam_detection": "POST /api/scam-detection",
            "session_info": "GET /api/session/{session_id}",
            "trigger_callback": "POST /api/trigger-callback/{session_id}"
        }
    }


# Catch-all for basic testing if they post to root
@app.post("/", tags=["root"])
async def root_post(request: Request):
    """
    Catch-all for POST requests to root, rerouting to scam detection logic if needed.
    """
    body = await request.json()
    return {
        "status": "success",
        "message": "Root POST received. Please use /api/scam-detection",
        "received_data": body
    }

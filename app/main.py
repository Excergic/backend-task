from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db
from app.api.v1 import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    print("Starting Stories Service...")
    await db.connect()
    
    yield
    
    # Shutdown
    print("Shutting down Stories Service...")
    await db.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready ephemeral Stories backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Stories Service API",
        "docs": "/docs",
        "health": "/healthz"
    }

# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.config import settings
# from app.database import db
# from app.api.v1 import auth
# from app.api.v1 import auth, uploads, stories, users, social, websocket


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for startup/shutdown events
#     """
#     # Startup
#     print("Starting Stories Service...")
#     await db.connect()
    
#     yield
    
#     # Shutdown
#     print("Shutting down Stories Service...")
#     await db.disconnect()


# # Initialize FastAPI app
# app = FastAPI(
#     title=settings.APP_NAME,
#     description="Production-ready ephemeral Stories backend",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth.router, prefix="/api/v1")
# app.include_router(uploads.router, prefix="/api/v1")
# app.include_router(stories.router, prefix="/api/v1")
# app.include_router(users.router, prefix="/api/v1")
# app.include_router(social.router, prefix="/api/v1")
# app.include_router(websocket.router, prefix="/api/v1")


# @app.get("/healthz")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "service": settings.APP_NAME
#     }


# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {
#         "message": "Stories Service API",
#         "docs": "/docs",
#         "health": "/healthz"
#     }

# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import db
from app.core.redis_client import redis_client
from app.api.v1 import auth, uploads, stories, users, social, websocket, cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    print("Starting Stories Service...")
    await db.connect()
    await redis_client.connect()
    
    yield
    
    # Shutdown
    print("Shutting down Stories Service...")
    await db.disconnect()
    await redis_client.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready ephemeral Stories backend with rate limiting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - configured from env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"]
)


# Custom exception handlers for proper 4xx/5xx responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        },
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (422) with detailed messages"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors (500)"""
    # Log the error (in production, use proper logging)
    print(f"Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc),
            "status_code": 500
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(cache.router, prefix="/api/v1") 


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    # Check Redis connection
    try:
        await redis_client.redis.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "redis": redis_status
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Stories Service API",
        "docs": "/docs",
        "health": "/healthz",
        "rate_limits": {
            "POST /stories": f"{settings.RATE_LIMIT_STORIES}/min",
            "POST /reactions": f"{settings.RATE_LIMIT_REACTIONS}/min",
            "POST /view": f"{settings.RATE_LIMIT_VIEWS}/min",
            "POST /follow": f"{settings.RATE_LIMIT_FOLLOW}/min"
        }
    }

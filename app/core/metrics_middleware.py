import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import http_requests_total, http_request_duration_seconds


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract route pattern (not full path with IDs)
        route = request.url.path
        for r in request.app.routes:
            match = r.matches(request.scope)
            if match[0] == 2:  # Full match
                route = r.path
                break
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            route=route,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            route=route
        ).observe(duration)
        
        return response

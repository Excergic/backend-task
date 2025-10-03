from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'route', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'route']
)

# Business Metrics - Stories
stories_created_total = Counter(
    'stories_created_total',
    'Total stories created',
    ['visibility']
)

story_views_total = Counter(
    'story_views_total',
    'Total story views',
    ['is_new_view']
)

reactions_total = Counter(
    'reactions_total',
    'Total reactions added',
    ['emoji']
)

# Business Metrics - Auth
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['result']  # success or failed
)

# Worker Metrics
stories_expired_total = Counter(
    'stories_expired_total',
    'Total stories expired by worker'
)

worker_latency_seconds = Histogram(
    'worker_latency_seconds',
    'Worker execution latency in seconds'
)

worker_iterations_total = Counter(
    'worker_iterations_total',
    'Total worker iterations'
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']  # followees, feed
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# System Metrics
active_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections'
)

# Rate Limit Metrics
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit violations',
    ['endpoint']
)


def get_metrics():
    """Generate Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

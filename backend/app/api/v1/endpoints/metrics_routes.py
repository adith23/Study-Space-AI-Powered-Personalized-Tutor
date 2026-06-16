"""Prometheus metrics endpoint for optional external monitoring."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Histogram,
                               generate_latest)

router = APIRouter(tags=["monitoring"])

# ── Counters & histograms ────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)
TASK_COUNT = Counter(
    "tasks_total",
    "Total async tasks dispatched",
    ["task_name", "status"],
)


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus-compatible metrics scrape endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

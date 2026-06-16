"""
FastAPI middleware that records Prometheus metrics for every request.

Captures:
  - http_requests_total: counter with method, path, status labels
  - http_request_duration_seconds: histogram with method, path labels

Works both locally and on Lambda. CloudWatch captures these via
the /metrics Prometheus endpoint, or they can be scraped by
any Prometheus-compatible system.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.endpoints.metrics_routes import REQUEST_COUNT, REQUEST_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track request counts and latency per endpoint."""

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        # Normalize path to avoid high-cardinality labels
        path = self._normalize_path(request.url.path)

        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Replace numeric path segments with placeholders to prevent
        Prometheus label explosion (e.g., /api/v1/videos/123 → /api/v1/videos/:id).
        """
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append(":id")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)

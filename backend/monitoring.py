"""
Prometheus metrics and monitoring helpers for ContextPilot.
"""
import re
from typing import Optional

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


_PATH_UUID_RE = re.compile(r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?=/|$)")


http_requests_total = Counter(
    "contextpilot_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "contextpilot_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

active_requests = Gauge(
    "contextpilot_http_active_requests",
    "Number of in-flight HTTP requests",
)

ai_requests_total = Counter(
    "contextpilot_ai_requests_total",
    "Total number of AI requests",
    ["provider", "status"],
)

ai_request_duration_seconds = Histogram(
    "contextpilot_ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0),
)

security_events_total = Counter(
    "contextpilot_security_events_total",
    "Total number of security-relevant events",
    ["event", "outcome"],
)


def normalize_path(path: str) -> str:
    """Normalize dynamic path segments to avoid high-cardinality metric labels."""
    normalized = _PATH_UUID_RE.sub("/:id", path)
    parts = normalized.split("/")
    for index, segment in enumerate(parts):
        if not segment:
            continue
        if len(segment) >= 12 and ("-" in segment or "_" in segment or any(char.isdigit() for char in segment)):
            parts[index] = ":id"
    return "/".join(parts)


def start_http_request() -> None:
    """Record an in-flight request start."""
    active_requests.inc()


def end_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Record request completion metrics."""
    normalized_path = normalize_path(path)
    http_requests_total.labels(method=method, path=normalized_path, status=str(status_code)).inc()
    http_request_duration_seconds.labels(method=method, path=normalized_path).observe(duration_seconds)
    active_requests.dec()


def record_ai_request(provider: Optional[str], status: str, duration_seconds: float) -> None:
    """Record AI provider request metrics."""
    provider_label = provider or "unknown"
    ai_requests_total.labels(provider=provider_label, status=status).inc()
    ai_request_duration_seconds.labels(provider=provider_label).observe(duration_seconds)


def record_security_event(event: str, outcome: str) -> None:
    """Record security-relevant events (auth/signing failures, etc.)."""
    security_events_total.labels(event=event, outcome=outcome).inc()


def get_metrics_payload() -> bytes:
    """Return Prometheus metrics payload."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Return Prometheus metrics content type."""
    return CONTENT_TYPE_LATEST

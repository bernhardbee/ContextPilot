"""
Tests for monitoring and observability endpoints.
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from main import app
from monitoring import get_metrics_payload, normalize_path, record_ai_request


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_normalize_path_replaces_dynamic_segments():
    """Dynamic path segments should be normalized for safe metric labels."""
    path = "/ai/conversations/123e4567-e89b-12d3-a456-426614174000/messages"
    normalized = normalize_path(path)
    assert normalized == "/ai/conversations/:id/messages"


def test_normalize_path_keeps_static_segments():
    """Static path segments should not be rewritten."""
    path = "/providers/conversations/settings"
    normalized = normalize_path(path)
    assert normalized == "/providers/conversations/settings"


def test_record_ai_request_exposes_prometheus_series():
    """Recording AI requests should appear in Prometheus payload."""
    record_ai_request(provider="openai", status="success", duration_seconds=0.12)

    payload = get_metrics_payload().decode("utf-8")
    assert 'contextpilot_ai_requests_total{provider="openai",status="success"}' in payload
    assert 'contextpilot_ai_request_duration_seconds_sum{provider="openai"}' in payload


def test_record_ai_request_uses_unknown_provider_label():
    """Missing provider names should be recorded as 'unknown'."""
    record_ai_request(provider=None, status="server_error", duration_seconds=0.07)

    payload = get_metrics_payload().decode("utf-8")
    assert 'contextpilot_ai_requests_total{provider="unknown",status="server_error"}' in payload


def test_metrics_endpoint_disabled_returns_404(monkeypatch):
    """Metrics endpoint should be hidden when monitoring is disabled."""
    monkeypatch.setattr(main.settings, "enable_metrics", False)

    with pytest.raises(HTTPException) as exc_info:
        main.metrics()

    assert exc_info.value.status_code == 404


def test_metrics_endpoint_enabled_returns_payload(monkeypatch):
    """Metrics endpoint should return Prometheus content when enabled."""
    monkeypatch.setattr(main.settings, "enable_metrics", True)

    response = main.metrics()

    assert response.status_code == 200
    assert "text/plain" in response.media_type


def test_request_middleware_emits_http_metrics(client, monkeypatch):
    """A normal request should be reflected in HTTP metrics output."""
    monkeypatch.setattr(main.settings, "enable_metrics", True)

    health_response = client.get("/health")
    assert health_response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics_payload = metrics_response.text
    assert 'contextpilot_http_requests_total{method="GET",path="/health",status="200"}' in metrics_payload

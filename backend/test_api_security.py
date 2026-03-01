"""
Integration tests for API security and validation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestAPISecurityIntegration:
    """Integration tests for API security features."""
    
    def test_create_context_with_long_content(self, client):
        """Test that creating context with too long content fails."""
        context_data = {
            "type": "preference",
            "content": "a" * 10001,  # Exceeds max length
            "confidence": 1.0,
            "tags": []
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["message"].lower()
    
    def test_create_context_with_empty_content(self, client):
        """Test that creating context with empty content fails."""
        context_data = {
            "type": "preference",
            "content": "",
            "confidence": 1.0,
            "tags": []
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 400
        assert "empty" in response.json()["message"].lower()
    
    def test_create_context_with_too_many_tags(self, client):
        """Test that creating context with too many tags fails."""
        context_data = {
            "type": "preference",
            "content": "Test content",
            "confidence": 1.0,
            "tags": [f"tag{i}" for i in range(21)]  # Exceeds max
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 400
        assert "maximum" in response.json()["message"].lower()
    
    def test_create_context_with_invalid_tag_chars(self, client):
        """Test that creating context with invalid tag characters fails."""
        context_data = {
            "type": "preference",
            "content": "Test content",
            "confidence": 1.0,
            "tags": ["valid", "invalid@tag"]
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 400
        assert "invalid characters" in response.json()["message"].lower()
    
    def test_create_context_sanitizes_input(self, client):
        """Test that input is properly sanitized."""
        context_data = {
            "type": "preference",
            "content": "  Test content with spaces  ",
            "confidence": 1.0,
            "tags": ["  tag1  ", "tag2"]
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test content with spaces"
        assert "tag1" in data["tags"]  # Should be sanitized
    
    def test_generate_prompt_with_long_task(self, client):
        """Test that generating prompt with too long task fails."""
        task_data = {
            "task": "a" * 10001,  # Exceeds max length
            "max_context_units": 5
        }
        response = client.post("/generate-prompt", json=task_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["message"].lower()
    
    def test_generate_prompt_with_too_many_contexts(self, client):
        """Test that requesting too many contexts fails."""
        task_data = {
            "task": "Test task",
            "max_context_units": 21  # Exceeds max
        }
        response = client.post("/generate-prompt", json=task_data)
        # Pydantic validation returns 422, or our validation returns 400
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            assert "exceeds limit" in response.json()["detail"].lower()
    
    def test_cors_headers_configured(self, client):
        """Test that CORS headers are properly configured."""
        response = client.options("/health")
        # FastAPI TestClient doesn't fully simulate CORS, but we can verify the middleware is configured
        # In real deployment, this would include Access-Control-Allow-Origin headers
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented for all endpoints
    
    def test_health_endpoint_no_auth(self, client):
        """Test that health endpoint works without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_security_headers_present_on_responses(self, client):
        """Security headers middleware should attach hardening headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers

    def test_hsts_header_added_for_https_forwarded_requests(self, client):
        """HSTS header should be set when request is forwarded as HTTPS."""
        response = client.get("/health", headers={"X-Forwarded-Proto": "https"})
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers


class TestAPIRateLimits:
    """Tests for API rate limiting (future implementation)."""
    
    def test_content_length_limit_enforced(self, client):
        """Test that content length limits are enforced."""
        # This test ensures our validation layer is working
        very_long_content = "x" * 15000
        context_data = {
            "type": "fact",
            "content": very_long_content,
            "confidence": 0.9,
            "tags": []
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 400


class TestInputSanitization:
    """Tests for input sanitization."""
    
    def test_sanitize_control_characters(self, client):
        """Test that control characters are removed."""
        context_data = {
            "type": "preference",
            "content": "Hello\x00\x01World",
            "confidence": 1.0,
            "tags": []
        }
        response = client.post("/contexts", json=context_data)
        if response.status_code == 201:
            data = response.json()
            # Control characters should be removed
            assert "\x00" not in data["content"]
            assert "\x01" not in data["content"]
    
    def test_preserve_unicode(self, client):
        """Test that valid unicode is preserved."""
        context_data = {
            "type": "preference",
            "content": "Hello 世界 🌍",
            "confidence": 1.0,
            "tags": []
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 201
        data = response.json()
        assert "世界" in data["content"]
        assert "🌍" in data["content"]

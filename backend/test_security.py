"""
Tests for security features.
"""
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from security import (
    verify_api_key,
    generate_request_signature,
    is_timestamp_fresh,
    verify_request_signature,
)
from monitoring import get_metrics_payload
from config import Settings


class TestAPIKeyAuthentication:
    """Tests for API key authentication."""
    
    @pytest.mark.asyncio
    async def test_verify_api_key_disabled(self):
        """Test that API key verification is bypassed when auth is disabled."""
        with patch('security.settings') as mock_settings:
            mock_settings.enable_auth = False
            result = await verify_api_key(None)
            assert result == "auth_disabled"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """Test that valid API key is accepted."""
        with patch('security.settings') as mock_settings:
            mock_settings.enable_auth = True
            mock_settings.api_key = "test-key-123"
            result = await verify_api_key("test-key-123")
            assert result == "test-key-123"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_missing(self):
        """Test that missing API key raises 401."""
        with patch('security.settings') as mock_settings:
            mock_settings.enable_auth = True
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(None)
            assert exc_info.value.status_code == 401
            assert "required" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test that invalid API key raises 401."""
        with patch('security.settings') as mock_settings:
            mock_settings.enable_auth = True
            mock_settings.api_key = "correct-key"
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("wrong-key")
            assert exc_info.value.status_code == 401
            assert "invalid" in str(exc_info.value.detail).lower()


class TestConfiguration:
    """Tests for configuration settings."""
    
    def test_settings_defaults(self):
        """Test that settings have sensible defaults."""
        settings = Settings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.max_content_length == 10000
        assert settings.max_contexts_per_request == 20
        assert settings.enable_auth == False
        assert settings.enable_request_signing == False
    
    def test_settings_cors_defaults(self):
        """Test that CORS settings have secure defaults."""
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "*" not in settings.cors_origins  # Should not allow all origins by default


class TestRequestSigning:
    """Tests for optional request-signing verification."""

    def _build_mock_request(self, method: str, path: str, body: bytes):
        request = Mock()
        request.method = method
        request.url = Mock(path=path)
        request.body = AsyncMock(return_value=body)
        return request

    def test_timestamp_freshness(self):
        """Timestamp freshness should be evaluated correctly."""
        current_timestamp = str(int(time.time()))
        stale_timestamp = str(int(time.time()) - 1000)

        assert is_timestamp_fresh(current_timestamp, max_age_seconds=300)
        assert not is_timestamp_fresh(stale_timestamp, max_age_seconds=300)

    @pytest.mark.asyncio
    async def test_verify_request_signature_disabled_bypasses(self):
        """When disabled, request signing should not block requests."""
        request = self._build_mock_request("POST", "/contexts", b'{"content":"x"}')

        with patch('security.settings') as mock_settings:
            mock_settings.enable_request_signing = False
            result = await verify_request_signature(request, None, None)
            assert result == "request_signing_disabled"

    @pytest.mark.asyncio
    async def test_verify_request_signature_valid(self):
        """Valid request signature should pass verification."""
        body = b'{"content":"signed"}'
        method = "POST"
        path = "/contexts"
        timestamp = str(int(time.time()))
        request = self._build_mock_request(method, path, body)

        signature = generate_request_signature(
            method=method,
            path=path,
            timestamp=timestamp,
            body=body,
            secret="test-signing-secret",
        )

        with patch('security.settings') as mock_settings:
            mock_settings.enable_request_signing = True
            mock_settings.request_signing_methods = ["POST", "PUT", "DELETE"]
            mock_settings.request_signing_secret = "test-signing-secret"
            mock_settings.request_signing_max_age_seconds = 300

            result = await verify_request_signature(request, signature, timestamp)
            assert result == "request_signature_valid"

    @pytest.mark.asyncio
    async def test_verify_request_signature_rejects_invalid_signature(self):
        """Invalid signatures should be rejected with 401."""
        body = b'{"content":"signed"}'
        request = self._build_mock_request("POST", "/contexts", body)

        with patch('security.settings') as mock_settings:
            mock_settings.enable_request_signing = True
            mock_settings.request_signing_methods = ["POST", "PUT", "DELETE"]
            mock_settings.request_signing_secret = "test-signing-secret"
            mock_settings.request_signing_max_age_seconds = 300

            with pytest.raises(HTTPException) as exc_info:
                await verify_request_signature(request, "invalid", str(int(time.time())))

            assert exc_info.value.status_code == 401
            assert "invalid request signature" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_verify_request_signature_rejects_stale_timestamp(self):
        """Expired timestamp should be rejected with 401."""
        body = b'{"content":"signed"}'
        request = self._build_mock_request("POST", "/contexts", body)

        with patch('security.settings') as mock_settings:
            mock_settings.enable_request_signing = True
            mock_settings.request_signing_methods = ["POST", "PUT", "DELETE"]
            mock_settings.request_signing_secret = "test-signing-secret"
            mock_settings.request_signing_max_age_seconds = 60

            with pytest.raises(HTTPException) as exc_info:
                await verify_request_signature(request, "anything", str(int(time.time()) - 600))

            assert exc_info.value.status_code == 401
            assert "expired" in str(exc_info.value.detail).lower()


class TestSecurityMetrics:
    """Tests for security observability metrics emission."""

    @pytest.mark.asyncio
    async def test_invalid_api_key_emits_security_metric(self):
        with patch('security.settings') as mock_settings:
            mock_settings.enable_auth = True
            mock_settings.api_key = "correct-key"
            with pytest.raises(HTTPException):
                await verify_api_key("wrong-key")

        payload = get_metrics_payload().decode("utf-8")
        assert 'contextpilot_security_events_total{event="api_key_auth",outcome="invalid_key"}' in payload

    @pytest.mark.asyncio
    async def test_invalid_signature_emits_security_metric(self):
        request = Mock()
        request.method = "POST"
        request.url = Mock(path="/contexts")
        request.body = AsyncMock(return_value=b'{"content":"x"}')

        with patch('security.settings') as mock_settings:
            mock_settings.enable_request_signing = True
            mock_settings.request_signing_methods = ["POST", "PUT", "DELETE"]
            mock_settings.request_signing_secret = "test-signing-secret"
            mock_settings.request_signing_max_age_seconds = 300

            with pytest.raises(HTTPException):
                await verify_request_signature(request, "bad-signature", str(int(time.time())))

        payload = get_metrics_payload().decode("utf-8")
        assert 'contextpilot_security_events_total{event="request_signing",outcome="invalid_signature"}' in payload

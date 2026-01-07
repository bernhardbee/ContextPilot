"""
Tests for security features.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from security import verify_api_key
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
    
    def test_settings_cors_defaults(self):
        """Test that CORS settings have secure defaults."""
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "*" not in settings.cors_origins  # Should not allow all origins by default

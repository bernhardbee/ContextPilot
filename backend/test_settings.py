"""
Tests for settings management functionality.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestSettings:
    """Test settings management endpoints."""
    
    def test_get_settings(self, client):
        """Test getting current settings."""
        response = client.get("/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert "openai_api_key_set" in data
        assert "anthropic_api_key_set" in data
        assert "default_ai_provider" in data
        assert "default_ai_model" in data
        assert "ai_temperature" in data
        assert "ai_max_tokens" in data
        
        # API key status should be boolean
        assert isinstance(data["openai_api_key_set"], bool)
        assert isinstance(data["anthropic_api_key_set"], bool)
        
        # Verify default values
        assert data["default_ai_provider"] == "openai"
        assert data["default_ai_model"] == "gpt-4-turbo-preview"
        assert data["ai_temperature"] == 0.7
        assert data["ai_max_tokens"] == 2000
    
    def test_update_settings_api_keys(self, client):
        """Test updating API keys."""
        settings_data = {
            "openai_api_key": "test-openai-key-123",
            "anthropic_api_key": "test-anthropic-key-456"
        }
        
        response = client.post("/settings", json=settings_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Settings updated successfully"
        assert "openai_api_key" in data["updated_fields"]
        assert "anthropic_api_key" in data["updated_fields"]
        
        # Verify settings were updated
        assert data["settings"]["openai_api_key_set"] == True
        assert data["settings"]["anthropic_api_key_set"] == True
    
    def test_update_settings_ai_config(self, client):
        """Test updating AI configuration."""
        settings_data = {
            "default_ai_provider": "anthropic",
            "default_ai_model": "claude-3-sonnet-20240229",
            "ai_temperature": 0.5,
            "ai_max_tokens": 1500
        }
        
        response = client.post("/settings", json=settings_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Settings updated successfully"
        assert set(data["updated_fields"]) == {
            "default_ai_provider", "default_ai_model", 
            "ai_temperature", "ai_max_tokens"
        }
        
        # Verify settings were updated
        settings = data["settings"]
        assert settings["default_ai_provider"] == "anthropic"
        assert settings["default_ai_model"] == "claude-3-sonnet-20240229"
        assert settings["ai_temperature"] == 0.5
        assert settings["ai_max_tokens"] == 1500
    
    def test_update_settings_partial(self, client):
        """Test partial settings update."""
        settings_data = {
            "ai_temperature": 1.2
        }
        
        response = client.post("/settings", json=settings_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Settings updated successfully"
        assert data["updated_fields"] == ["ai_temperature"]
        assert data["settings"]["ai_temperature"] == 1.2
    
    def test_update_settings_empty(self, client):
        """Test empty settings update."""
        response = client.post("/settings", json={})
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Settings updated successfully"
        assert data["updated_fields"] == []
    
    def test_update_settings_validation(self, client):
        """Test settings validation."""
        # Invalid temperature (too high)
        response = client.post("/settings", json={"ai_temperature": 3.0})
        assert response.status_code == 422
        
        # Invalid max tokens (too low) 
        response = client.post("/settings", json={"ai_max_tokens": 0})
        assert response.status_code == 422
        
        # Invalid max tokens (too high)
        response = client.post("/settings", json={"ai_max_tokens": 5000})
        assert response.status_code == 422
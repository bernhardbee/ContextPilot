"""
Tests for settings management functionality.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
import main
from models import SecurityEvent


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
        assert data["default_ai_model"] == "gpt-4o"
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
        response = client.post("/settings", json={"ai_max_tokens": 20000})
        assert response.status_code == 422

    def test_validate_provider_connection_endpoint(self, client, monkeypatch):
        """Validate provider endpoint returns provider validation result."""
        def fake_validate(provider_name, model=None):
            return {
                "provider": provider_name,
                "valid": True,
                "message": "OpenAI connection and API key are valid.",
                "checked_model": model or "gpt-4o"
            }

        monkeypatch.setattr(main.ai_service, "validate_provider_connection", fake_validate)

        response = client.post("/providers/openai/validate", params={"model": "gpt-4o"})
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["valid"] is True
        assert "api key" in data["message"].lower()
        assert data["checked_model"] == "gpt-4o"

    def test_ai_chat_returns_actionable_client_error_detail(self, client, monkeypatch):
        """AI chat should expose provider-specific client errors as 400 details."""
        def fake_generate_response(**kwargs):
            raise ValueError("OpenAI authentication failed. The configured API key was rejected.")

        monkeypatch.setattr(main.ai_service, "generate_response", fake_generate_response)

        response = client.post("/ai/chat", json={"task": "hello", "provider": "openai", "model": "gpt-4o"})
        assert response.status_code == 400
        message = response.json().get("message", "")
        assert "authentication failed" in message.lower()

    def test_rotate_api_key_requires_auth_enabled(self, client, monkeypatch):
        """Rotation endpoint should reject when auth is disabled."""
        monkeypatch.setattr(main.settings, "enable_auth", False)
        monkeypatch.setattr(main.settings, "enable_request_signing", False)

        response = client.post("/security/api-key/rotate")
        assert response.status_code == 400
        assert "enable authentication" in response.json().get("message", "").lower()

    def test_rotate_api_key_success_persists_hash_and_metadata(self, client, monkeypatch):
        """Rotation endpoint should return new key and persist only hashed value/metadata."""

        class FakeStore:
            def __init__(self):
                self.values = {}

            def get(self, key):
                return self.values.get(key)

            def set(self, key, value):
                self.values[key] = value

            def delete(self, key):
                self.values.pop(key, None)

        fake_store = FakeStore()
        fake_store.set("api_key", "legacy-plain")

        monkeypatch.setattr(main.settings, "enable_auth", True)
        monkeypatch.setattr(main.settings, "enable_request_signing", False)
        monkeypatch.setattr(main.settings, "api_key", "current-api-key")
        monkeypatch.setattr(main.settings, "api_key_hash", "")
        monkeypatch.setattr(main.settings_store_module, "settings_store", fake_store)
        monkeypatch.setattr(main.secrets, "token_urlsafe", lambda _: "rotated-api-key")

        response = client.post("/security/api-key/rotate", headers={"X-API-Key": "current-api-key"})
        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "API key rotated successfully"
        assert data["api_key"] == "rotated-api-key"
        assert "rotated_at" in data

        assert fake_store.get("api_key") is None
        assert fake_store.get("api_key_hash") == main.hash_api_key("rotated-api-key")
        assert fake_store.get("api_key_last_rotated_at") == data["rotated_at"]
        assert fake_store.get("api_key_last_used_at") == data["rotated_at"]
        assert fake_store.get("api_key_created_at") is not None

    def test_get_security_events_endpoint(self, client, monkeypatch):
        """Security events endpoint should return persisted event payloads."""
        monkeypatch.setattr(main.settings, "enable_auth", False)

        sample_event = SecurityEvent(
            id="evt-1",
            event="api_key_auth",
            outcome="valid_key",
            request_id="req-1",
            method="GET",
            path="/stats",
            client_ip="127.0.0.1",
            actor="api_key:test***",
            details={"source": "test"},
            created_at=datetime.utcnow(),
        )

        monkeypatch.setattr(main, "list_security_events", lambda **kwargs: [sample_event])

        response = client.get("/security/events")
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["events"][0]["event"] == "api_key_auth"
        assert payload["events"][0]["request_id"] == "req-1"

    def test_get_security_events_bounds_limit_and_offset(self, client, monkeypatch):
        """Security events endpoint should clamp pagination inputs to safe bounds."""
        monkeypatch.setattr(main.settings, "enable_auth", False)

        captured = {}

        def fake_list_security_events(limit, offset, event=None, outcome=None, request_id=None):
            captured["limit"] = limit
            captured["offset"] = offset
            return []

        monkeypatch.setattr(main, "list_security_events", fake_list_security_events)

        response = client.get("/security/events", params={"limit": 500, "offset": -7})
        assert response.status_code == 200
        assert captured["limit"] == 200
        assert captured["offset"] == 0
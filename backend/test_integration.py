"""
Integration tests for ContextPilot end-to-end functionality.
Tests the full flow from context creation to AI response generation.

NOTE: These tests require a running backend server on http://localhost:8000
Start the server with: python main.py
The server should be configured with test API keys in .env or environment.
"""
import os
import pytest
import requests
from typing import Dict, Any
from fastapi.testclient import TestClient
from httpx import HTTPStatusError

from main import app

@pytest.fixture
def api_client():
    """Fixture providing API client using FastAPI TestClient."""
    class APIClient:
        def __init__(self, client: TestClient):
            self.client = client
        
        def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
            response = self.client.get(endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        
        def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
            response = self.client.post(endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        
        def delete(self, endpoint: str, **kwargs) -> None:
            response = self.client.delete(endpoint, **kwargs)
            response.raise_for_status()
    
    return APIClient(TestClient(app))

class TestHealthAndStats:
    """Test basic health and statistics endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        result = api_client.get("/health")
        assert result["status"] == "healthy"
        assert "timestamp" in result
    
    def test_stats_endpoint(self, api_client):
        """Test statistics endpoint."""
        result = api_client.get("/stats")
        assert "total_contexts" in result
        assert "active_contexts" in result
        assert "contexts_by_type" in result

class TestContextCRUD:
    """Test context CRUD operations."""

    def _create_context(self, api_client) -> str:
        """Helper to create a context and return its ID."""
        context_data = {
            "type": "preference",
            "content": "I prefer functional programming style",
            "confidence": 0.9,
            "tags": ["programming", "style"]
        }
        result = api_client.post("/contexts", json=context_data)
        return result["id"]
    
    def test_create_context(self, api_client):
        """Test creating a new context."""
        context_data = {
            "type": "preference",
            "content": "I prefer functional programming style",
            "confidence": 0.9,
            "tags": ["programming", "style"]
        }
        result = api_client.post("/contexts", json=context_data)
        assert result["type"] == "preference"
        assert result["content"] == context_data["content"]
        assert result["confidence"] == 0.9
        assert "id" in result
    
    def test_list_contexts(self, api_client):
        """Test listing all contexts."""
        # Create a context first
        self._create_context(api_client)
        
        # List contexts
        result = api_client.get("/contexts")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_specific_context(self, api_client):
        """Test retrieving a specific context."""
        # Create a context
        context_id = self._create_context(api_client)
        
        # Get it back
        result = api_client.get(f"/contexts/{context_id}")
        assert result["id"] == context_id
        assert result["type"] == "preference"
    
    def test_delete_context(self, api_client):
        """Test deleting a context."""
        # Create a context
        context_id = self._create_context(api_client)
        
        # Delete it
        api_client.delete(f"/contexts/{context_id}")
        
        # Verify it's gone
        with pytest.raises(HTTPStatusError):
            api_client.get(f"/contexts/{context_id}")

class TestPromptGeneration:
    """Test prompt generation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_contexts(self, api_client):
        """Create test contexts before each test."""
        self.context_ids = []
        contexts = [
            {
                "type": "preference",
                "content": "I prefer Python over JavaScript for backend development",
                "confidence": 0.95,
                "tags": ["programming", "backend"]
            },
            {
                "type": "goal",
                "content": "Build a context management system for AI applications",
                "confidence": 1.0,
                "tags": ["project", "ai"]
            },
            {
                "type": "fact",
                "content": "I have 5 years of experience with Python and FastAPI",
                "confidence": 1.0,
                "tags": ["skills", "experience"]
            }
        ]
        
        for context_data in contexts:
            result = api_client.post("/contexts", json=context_data)
            self.context_ids.append(result["id"])
        
        yield
        
        # Cleanup
        for context_id in self.context_ids:
            try:
                api_client.delete(f"/contexts/{context_id}")
            except:
                pass
    
    def test_generate_prompt(self, api_client):
        """Test generating a contextualized prompt."""
        task_data = {
            "task": "Write a Python function to process user data",
            "max_context_units": 5
        }
        
        result = api_client.post("/generate-prompt", json=task_data)
        
        assert result["original_task"] == task_data["task"]
        assert "generated_prompt" in result
        assert "relevant_context" in result
        assert isinstance(result["relevant_context"], list)
        assert len(result["relevant_context"]) > 0
        
        # Check that relevant context has relevance scores
        for ranked_context in result["relevant_context"]:
            assert "context_unit" in ranked_context
            assert "relevance_score" in ranked_context
            assert 0 <= ranked_context["relevance_score"] <= 1
    
    def test_generate_compact_prompt(self, api_client):
        """Test generating a compact prompt."""
        task_data = {
            "task": "Explain the main architectural decisions",
            "max_context_units": 3
        }
        
        result = api_client.post("/generate-prompt/compact", json=task_data)
        
        assert result["original_task"] == task_data["task"]
        assert "generated_prompt" in result
        # Compact format should be shorter
        assert len(result["generated_prompt"]) > 0

class TestAIIntegration:
    """Test AI integration endpoints (without actual API calls)."""
    
    @pytest.fixture(autouse=True)
    def setup_contexts(self, api_client):
        """Create test contexts before each test."""
        self.context_ids = []
        contexts = [
            {
                "type": "preference",
                "content": "I prefer concise technical explanations",
                "confidence": 0.9,
                "tags": ["communication"]
            },
            {
                "type": "fact",
                "content": "This is a context management system for AI applications",
                "confidence": 1.0,
                "tags": ["project", "description"]
            }
        ]
        
        for context_data in contexts:
            result = api_client.post("/contexts", json=context_data)
            self.context_ids.append(result["id"])
        
        yield
        
        # Cleanup
        for context_id in self.context_ids:
            try:
                api_client.delete(f"/contexts/{context_id}")
            except:
                pass
    
    def test_ai_chat_endpoint_exists(self, api_client):
        """Test that AI chat endpoint is available (will fail without API key)."""
        task_data = {
            "task": "What is this system for?",
            "max_context_units": 3
        }
        
        # This should return an error about API key, but endpoint should exist
        try:
            result = api_client.post("/ai/chat", json=task_data)
            # If it succeeds, check structure
            assert "conversation_id" in result or "detail" in result
        except HTTPStatusError as e:
            # Expected if no valid API key (can be 400, 500, 401, 403)
            assert e.response.status_code in [400, 500, 401, 403]
    
    def test_list_conversations_endpoint(self, api_client):
        """Test listing conversations endpoint."""
        result = api_client.get("/ai/conversations")
        # Can be a list or a paginated response
        assert isinstance(result, (list, dict))
        if isinstance(result, dict):
            assert "conversations" in result or "items" in result or len(result) == 0

class TestEndToEnd:
    """End-to-end workflow tests."""
    
    def test_full_workflow(self, api_client):
        """Test complete workflow from context creation to prompt generation."""
        # 1. Create contexts
        contexts_created = []
        context_data = [
            {
                "type": "preference",
                "content": "I value code readability and maintainability",
                "confidence": 1.0,
                "tags": ["coding", "principles"]
            },
            {
                "type": "decision",
                "content": "Use FastAPI for REST API development",
                "confidence": 0.95,
                "tags": ["architecture", "technology"]
            }
        ]
        
        for ctx in context_data:
            result = api_client.post("/contexts", json=ctx)
            contexts_created.append(result["id"])
        
        # 2. Verify contexts were created
        all_contexts = api_client.get("/contexts")
        assert len(all_contexts) >= len(contexts_created)
        
        # 3. Generate prompt
        task = "Design a new API endpoint for user management"
        prompt_result = api_client.post("/generate-prompt", json={
            "task": task,
            "max_context_units": 10
        })
        
        assert prompt_result["original_task"] == task
        assert len(prompt_result["generated_prompt"]) > 0
        assert len(prompt_result["relevant_context"]) > 0
        
        # 4. Verify relevant context includes our contexts
        relevant_ids = [rc["context_unit"]["id"] for rc in prompt_result["relevant_context"]]
        assert any(cid in relevant_ids for cid in contexts_created)
        
        # 5. Check stats
        stats = api_client.get("/stats")
        assert stats["active_contexts"] >= len(contexts_created)
        
        # 6. Cleanup
        for context_id in contexts_created:
            api_client.delete(f"/contexts/{context_id}")
        
        # 7. Verify cleanup
        remaining_contexts = api_client.get("/contexts")
        remaining_ids = [ctx["id"] for ctx in remaining_contexts]
        assert not any(cid in remaining_ids for cid in contexts_created)

class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_create_context_invalid_type(self, api_client):
        """Test creating context with invalid type."""
        context_data = {
            "type": "invalid_type",
            "content": "Test content",
            "confidence": 0.9
        }
        
        with pytest.raises(HTTPStatusError) as exc_info:
            api_client.post("/contexts", json=context_data)
        assert exc_info.value.response.status_code == 422
    
    def test_create_context_invalid_confidence(self, api_client):
        """Test creating context with invalid confidence."""
        context_data = {
            "type": "preference",
            "content": "Test content",
            "confidence": 1.5  # Invalid: must be 0-1
        }
        
        with pytest.raises(HTTPStatusError) as exc_info:
            api_client.post("/contexts", json=context_data)
        assert exc_info.value.response.status_code == 422
    
    def test_get_nonexistent_context(self, api_client):
        """Test retrieving a context that doesn't exist."""
        with pytest.raises(HTTPStatusError) as exc_info:
            api_client.get("/contexts/nonexistent-id-12345")
        assert exc_info.value.response.status_code == 404
    
    def test_generate_prompt_empty_task(self, api_client):
        """Test generating prompt with empty task."""
        with pytest.raises(HTTPStatusError) as exc_info:
            api_client.post("/generate-prompt", json={"task": ""})
        # Can be 400 or 422 depending on validation layer
        assert exc_info.value.response.status_code in [400, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

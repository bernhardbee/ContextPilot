"""
Integration tests for prompt logging API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestPromptLogAPI:
    """Tests for prompt logging API endpoints."""
    
    def test_prompt_generation_creates_log(self, client):
        """Test that generating a prompt creates a log entry."""
        # First, create a context
        context_data = {
            "type": "preference",
            "content": "Test preference for logging",
            "confidence": 1.0,
            "tags": ["test"]
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 201
        
        # Generate a prompt
        task_data = {
            "task": "Test task for logging",
            "max_context_units": 5
        }
        response = client.post("/generate-prompt", json=task_data)
        assert response.status_code == 200
        
        # Check that logs were created
        response = client.get("/prompt-logs?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_returned"] >= 1
        assert len(data["logs"]) >= 1
        
        # Verify log structure
        log = data["logs"][0]
        assert "log_id" in log
        assert "timestamp" in log
        assert "original_task" in log
        assert "generated_prompt" in log
        assert "prompt_type" in log
        assert log["prompt_type"] == "full"
    
    def test_compact_prompt_generation_creates_log(self, client):
        """Test that generating a compact prompt creates a log entry."""
        # Create a context
        context_data = {
            "type": "goal",
            "content": "Test goal",
            "confidence": 1.0,
            "tags": []
        }
        client.post("/contexts", json=context_data)
        
        # Generate compact prompt
        task_data = {
            "task": "Test compact task",
            "max_context_units": 3
        }
        response = client.post("/generate-prompt/compact", json=task_data)
        assert response.status_code == 200
        
        # Check logs
        response = client.get("/prompt-logs?limit=1&prompt_type=compact")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_returned"] >= 1
        log = data["logs"][0]
        assert log["prompt_type"] == "compact"
    
    def test_get_prompt_logs_pagination(self, client):
        """Test pagination of prompt logs."""
        # Generate multiple prompts
        for i in range(5):
            task_data = {
                "task": f"Test task {i}",
                "max_context_units": 2
            }
            client.post("/generate-prompt", json=task_data)
        
        # Test limit
        response = client.get("/prompt-logs?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 2
        assert data["limit"] == 2
        
        # Test offset
        response = client.get("/prompt-logs?limit=2&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 1
    
    def test_get_prompt_logs_invalid_limit(self, client):
        """Test that invalid limit values are rejected."""
        # Limit too high
        response = client.get("/prompt-logs?limit=2000")
        assert response.status_code == 400
        assert "exceed 1000" in response.json()["detail"].lower()
        
        # Limit too low
        response = client.get("/prompt-logs?limit=0")
        assert response.status_code == 400
        assert "at least 1" in response.json()["detail"].lower()
    
    def test_get_prompt_logs_invalid_type(self, client):
        """Test that invalid prompt_type values are rejected."""
        response = client.get("/prompt-logs?prompt_type=invalid")
        assert response.status_code == 400
        assert "must be 'full' or 'compact'" in response.json()["detail"]
    
    def test_get_prompt_log_by_id(self, client):
        """Test retrieving a specific log by ID."""
        # Generate a prompt
        task_data = {
            "task": "Test task for ID lookup",
            "max_context_units": 2
        }
        client.post("/generate-prompt", json=task_data)
        
        # Get logs and extract an ID
        response = client.get("/prompt-logs?limit=1")
        assert response.status_code == 200
        log_id = response.json()["logs"][0]["log_id"]
        
        # Get specific log
        response = client.get(f"/prompt-logs/{log_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["log_id"] == log_id
    
    def test_get_nonexistent_log_by_id(self, client):
        """Test that requesting nonexistent log returns 404."""
        response = client.get("/prompt-logs/prompt-999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_stats_includes_prompt_generation(self, client):
        """Test that /stats endpoint includes prompt generation stats."""
        # Generate some prompts
        for i in range(3):
            task_data = {
                "task": f"Task {i}",
                "max_context_units": 2
            }
            client.post("/generate-prompt" if i < 2 else "/generate-prompt/compact", json=task_data)
        
        # Check stats
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "prompt_generation" in data
        prompt_stats = data["prompt_generation"]
        
        assert "total_logs" in prompt_stats
        assert prompt_stats["total_logs"] >= 3
        assert "logs_by_type" in prompt_stats
    
    def test_export_prompt_logs(self, client):
        """Test exporting logs to JSON file."""
        # Generate a prompt
        task_data = {
            "task": "Test export",
            "max_context_units": 2
        }
        client.post("/generate-prompt", json=task_data)
        
        # Export logs
        response = client.post("/prompt-logs/export")
        assert response.status_code == 200
        data = response.json()
        
        assert "filepath" in data
        assert "timestamp" in data
        assert "prompt_logs_" in data["filepath"]
    
    def test_clear_prompt_logs(self, client):
        """Test clearing all logs."""
        # Generate some prompts
        for i in range(3):
            task_data = {
                "task": f"Task {i}",
                "max_context_units": 2
            }
            client.post("/generate-prompt", json=task_data)
        
        # Verify logs exist
        response = client.get("/prompt-logs?limit=100")
        initial_count = response.json()["total_returned"]
        assert initial_count >= 3
        
        # Clear logs
        response = client.delete("/prompt-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["logs_cleared"] >= 3
        
        # Verify logs are cleared
        response = client.get("/prompt-logs?limit=100")
        assert response.json()["total_returned"] == 0
    
    def test_log_contains_context_information(self, client):
        """Test that logs contain detailed context information."""
        # Create multiple contexts
        contexts = []
        for i in range(3):
            context_data = {
                "type": "preference" if i < 2 else "goal",
                "content": f"Context {i}",
                "confidence": 1.0,
                "tags": [f"tag{i}"]
            }
            response = client.post("/contexts", json=context_data)
            contexts.append(response.json())
        
        # Generate prompt
        task_data = {
            "task": "Task using multiple contexts",
            "max_context_units": 10
        }
        response = client.post("/generate-prompt", json=task_data)
        assert response.status_code == 200
        
        # Check log details
        response = client.get("/prompt-logs?limit=1")
        log = response.json()["logs"][0]
        
        assert "context_ids" in log
        assert "context_types" in log
        assert "num_contexts_used" in log
        assert log["num_contexts_used"] > 0
        
        # Verify context types aggregation (should exist and be positive)
        if "preference" in log["context_types"]:
            assert log["context_types"]["preference"] > 0
        if "goal" in log["context_types"]:
            assert log["context_types"]["goal"] > 0

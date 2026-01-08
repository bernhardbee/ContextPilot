"""
Test cases for import/export and search/filter endpoints.
"""
import pytest
import json
import io
from fastapi.testclient import TestClient
from main import app
from models import ContextType, ContextUnitCreate
from config import settings

client = TestClient(app)

# API auth headers (auth is disabled by default in settings)
headers = {}


class TestImportExport:
    """Tests for context import/export functionality."""
    
    def test_export_json(self):
        """Test exporting contexts as JSON."""
        response = client.get("/contexts/export?format=json", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Verify JSON structure
        data = json.loads(response.content)
        assert "export_date" in data
        assert "total_contexts" in data
        assert "contexts" in data
        assert isinstance(data["contexts"], list)
    
    def test_export_csv(self):
        """Test exporting contexts as CSV."""
        response = client.get("/contexts/export?format=csv", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        
        # Verify CSV has header
        content = response.content.decode()
        lines = content.strip().split('\n')
        assert len(lines) >= 1  # At least header
        assert "id" in lines[0]
        assert "type" in lines[0]
        assert "content" in lines[0]
    
    def test_export_invalid_format(self):
        """Test export with invalid format."""
        response = client.get("/contexts/export?format=xml", headers=headers)
        assert response.status_code == 400
        data = response.json()
        # Handle both 'detail' and 'message' keys
        error_msg = data.get('detail') or data.get('message', '')
        assert "unsupported format" in error_msg.lower()
    
    def test_import_json(self):
        """Test importing contexts from JSON."""
        # Create test data
        import_data = {
            "export_date": "2026-01-08T00:00:00",
            "total_contexts": 1,
            "contexts": [
                {
                    "type": "preference",
                    "content": "Test import context",
                    "confidence": 0.9,
                    "tags": ["test", "import"],
                    "source": "test",
                    "status": "active"
                }
            ]
        }
        
        # Create file-like object
        json_file = io.BytesIO(json.dumps(import_data).encode())
        
        # Upload file
        response = client.post(
            "/contexts/import",
            files={"file": ("test_contexts.json", json_file, "application/json")},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "imported" in data
        assert "skipped" in data
        assert data["imported"] >= 0
    
    def test_import_invalid_json(self):
        """Test import with invalid JSON."""
        # Create invalid JSON file
        json_file = io.BytesIO(b"not valid json")
        
        response = client.post(
            "/contexts/import",
            files={"file": ("test.json", json_file, "application/json")},
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        # Handle both 'detail' and 'message' keys
        error_msg = data.get('detail') or data.get('message', '')
        assert "json" in error_msg.lower()
    
    def test_import_non_json_file(self):
        """Test import with non-JSON file."""
        txt_file = io.BytesIO(b"some text content")
        
        response = client.post(
            "/contexts/import",
            files={"file": ("test.txt", txt_file, "text/plain")},
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        # Handle both 'detail' and 'message' keys
        error_msg = data.get('detail') or data.get('message', '')
        assert "json" in error_msg.lower()


class TestSearchAndFilter:
    """Tests for search and filter functionality."""
    
    def test_list_contexts_with_type_filter(self):
        """Test listing contexts filtered by type."""
        response = client.get("/contexts?type=preference", headers=headers)
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
        # If there are results, verify they match the filter
        for context in contexts:
            assert context["type"] == "preference"
    
    def test_list_contexts_with_invalid_type(self):
        """Test listing contexts with invalid type filter."""
        response = client.get("/contexts?type=invalid_type", headers=headers)
        assert response.status_code == 400
        data = response.json()
        # Handle both 'detail' and 'message' keys
        error_msg = data.get('detail') or data.get('message', '')
        assert "invalid" in error_msg.lower() and "type" in error_msg.lower()
    
    def test_list_contexts_with_status_filter(self):
        """Test listing contexts filtered by status."""
        response = client.get("/contexts?status_filter=active", headers=headers)
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
        for context in contexts:
            assert context["status"] == "active"
    
    def test_list_contexts_with_invalid_status(self):
        """Test listing contexts with invalid status filter."""
        response = client.get("/contexts?status_filter=invalid_status", headers=headers)
        assert response.status_code == 400
        data = response.json()
        # Handle both 'detail' and 'message' keys
        error_msg = data.get('detail') or data.get('message', '')
        assert "invalid" in error_msg.lower() and "status" in error_msg.lower()
    
    def test_list_contexts_with_tags_filter(self):
        """Test listing contexts filtered by tags."""
        response = client.get("/contexts?tags=python,coding", headers=headers)
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
    
    def test_list_contexts_with_search(self):
        """Test listing contexts with search term."""
        response = client.get("/contexts?search=test", headers=headers)
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
    
    def test_list_contexts_with_multiple_filters(self):
        """Test listing contexts with multiple filters."""
        response = client.get(
            "/contexts?type=preference&tags=coding&search=python&limit=10",
            headers=headers
        )
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
        assert len(contexts) <= 10
    
    def test_list_contexts_with_limit(self):
        """Test listing contexts with limit."""
        response = client.get("/contexts?limit=5", headers=headers)
        assert response.status_code == 200
        contexts = response.json()
        assert isinstance(contexts, list)
        assert len(contexts) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

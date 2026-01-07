"""
Unit tests for validation and security modules.
"""
import pytest
from fastapi import HTTPException
from validators import (
    validate_content_length,
    validate_tags,
    sanitize_string
)


class TestContentValidation:
    """Tests for content validation."""
    
    def test_validate_content_valid(self):
        """Test that valid content passes validation."""
        content = "This is valid content."
        # Should not raise
        validate_content_length(content)
    
    def test_validate_content_empty(self):
        """Test that empty content raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_content_length("")
        assert exc_info.value.status_code == 400
        assert "empty" in str(exc_info.value.detail).lower()
    
    def test_validate_content_whitespace_only(self):
        """Test that whitespace-only content raises error."""
        with pytest.raises(HTTPException) as exc_info:
            validate_content_length("   \n\t  ")
        assert exc_info.value.status_code == 400
    
    def test_validate_content_too_long(self):
        """Test that content exceeding max length raises error."""
        # Create content longer than default max (10000 chars)
        long_content = "a" * 10001
        with pytest.raises(HTTPException) as exc_info:
            validate_content_length(long_content)
        assert exc_info.value.status_code == 400
        assert "exceeds maximum" in str(exc_info.value.detail).lower()
    
    def test_validate_content_at_limit(self):
        """Test that content at exactly the limit is valid."""
        content_at_limit = "a" * 10000
        # Should not raise
        validate_content_length(content_at_limit)


class TestTagValidation:
    """Tests for tag validation."""
    
    def test_validate_tags_valid(self):
        """Test that valid tags pass validation."""
        tags = ["python", "machine-learning", "api_design"]
        # Should not raise
        validate_tags(tags)
    
    def test_validate_tags_empty_list(self):
        """Test that empty tag list is valid."""
        # Should not raise
        validate_tags([])
    
    def test_validate_tags_too_many(self):
        """Test that exceeding max tag count raises error."""
        tags = [f"tag{i}" for i in range(21)]  # Default max is 20
        with pytest.raises(HTTPException) as exc_info:
            validate_tags(tags)
        assert exc_info.value.status_code == 400
        assert "maximum" in str(exc_info.value.detail).lower()
    
    def test_validate_tags_empty_tag(self):
        """Test that empty tag raises error."""
        tags = ["valid", ""]
        with pytest.raises(HTTPException) as exc_info:
            validate_tags(tags)
        assert exc_info.value.status_code == 400
        assert "empty" in str(exc_info.value.detail).lower()
    
    def test_validate_tags_whitespace_only(self):
        """Test that whitespace-only tag raises error."""
        tags = ["valid", "   "]
        with pytest.raises(HTTPException) as exc_info:
            validate_tags(tags)
        assert exc_info.value.status_code == 400
    
    def test_validate_tags_too_long(self):
        """Test that tag exceeding max length raises error."""
        tags = ["a" * 51]  # Default max is 50
        with pytest.raises(HTTPException) as exc_info:
            validate_tags(tags)
        assert exc_info.value.status_code == 400
        assert "exceeds maximum length" in str(exc_info.value.detail).lower()
    
    def test_validate_tags_invalid_characters(self):
        """Test that tags with invalid characters raise error."""
        invalid_tags = [
            "tag@invalid",
            "tag#invalid",
            "tag$invalid",
            "tag%invalid"
        ]
        for tag in invalid_tags:
            with pytest.raises(HTTPException) as exc_info:
                validate_tags([tag])
            assert exc_info.value.status_code == 400
            assert "invalid characters" in str(exc_info.value.detail).lower()
    
    def test_validate_tags_valid_special_chars(self):
        """Test that valid special characters in tags are allowed."""
        tags = ["python-3", "my_tag", "tag with spaces"]
        # Should not raise
        validate_tags(tags)


class TestSanitization:
    """Tests for string sanitization."""
    
    def test_sanitize_normal_string(self):
        """Test that normal strings pass through unchanged."""
        text = "This is a normal string."
        assert sanitize_string(text) == text
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text = "Hello\x00World"
        assert sanitize_string(text) == "HelloWorld"
    
    def test_sanitize_removes_control_chars(self):
        """Test that control characters are removed (except newlines/tabs)."""
        text = "Hello\x01\x02World"
        assert sanitize_string(text) == "HelloWorld"
    
    def test_sanitize_preserves_newlines(self):
        """Test that newlines are preserved."""
        text = "Line 1\nLine 2"
        assert sanitize_string(text) == text
    
    def test_sanitize_preserves_tabs(self):
        """Test that tabs are preserved."""
        text = "Column1\tColumn2"
        assert sanitize_string(text) == text
    
    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        text = "  Hello World  "
        assert sanitize_string(text) == "Hello World"
    
    def test_sanitize_empty_string(self):
        """Test that empty string returns empty string."""
        assert sanitize_string("") == ""
    
    def test_sanitize_unicode(self):
        """Test that unicode characters are preserved."""
        text = "Hello 世界 🌍"
        assert sanitize_string(text) == text

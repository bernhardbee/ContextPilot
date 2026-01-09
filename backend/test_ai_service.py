"""
Tests for AI service integration.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ai_service import AIService
from models import GeneratedPrompt, RankedContextUnit, ContextUnit, ContextType
from database import Base, engine


@pytest.fixture(scope="function")
def setup_db():
    """Create database tables for tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def ai_service_instance(setup_db):
    """Create an AI service instance."""
    return AIService()


@pytest.fixture
def sample_prompt():
    """Create a sample generated prompt."""
    context = ContextUnit(
        type=ContextType.PREFERENCE,
        content="I prefer concise answers"
    )
    ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
    
    return GeneratedPrompt(
        original_task="What is Python?",
        relevant_context=[ranked],
        generated_prompt="Context: I prefer concise answers\n\nTask: What is Python?"
    )


class TestAIService:
    """Tests for AIService."""
    
    @patch('ai_service.openai')
    def test_generate_openai_response(self, mock_openai, ai_service_instance, sample_prompt):
        """Test generating a response with OpenAI."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {'content': 'Python is a programming language'}
        mock_response.choices[0].finish_reason = 'stop'
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 50
        
        mock_openai.ChatCompletion.create = Mock(return_value=mock_response)
        mock_openai.api_key = "test-key"
        ai_service_instance.openai_client = mock_openai
        
        # Generate response
        response, conversation = ai_service_instance.generate_response(
            task="What is Python?",
            generated_prompt=sample_prompt,
            context_ids=["ctx-1"],
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=100
        )
        
        assert response == 'Python is a programming language'
        assert conversation.provider == 'openai'
        assert conversation.model == 'gpt-4'
        assert conversation.task == "What is Python?"
    
    @pytest.mark.asyncio
    async def test_generate_without_api_key_raises_error(self, ai_service_instance, sample_prompt):
        """Test that generating without API key raises an error."""
        ai_service_instance.openai_client = None
        ai_service_instance.anthropic_client = None
        
        with pytest.raises(ValueError, match="API key not configured"):
            await ai_service_instance.generate_response(
                task="Test",
                generated_prompt=sample_prompt,
                context_ids=[],
                provider="openai"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_provider_raises_error(self, ai_service_instance, sample_prompt):
        """Test that invalid provider raises an error."""
        with pytest.raises(ValueError, match="Unknown AI provider"):
            await ai_service_instance.generate_response(
                task="Test",
                generated_prompt=sample_prompt,
                context_ids=[],
                provider="invalid"
            )
    
    def test_get_nonexistent_conversation(self, ai_service_instance):
        """Test getting a conversation that doesn't exist."""
        result = ai_service_instance.get_conversation("nonexistent-id")
        assert result is None
    
    def test_list_conversations_empty(self, ai_service_instance):
        """Test listing conversations when none exist."""
        conversations = ai_service_instance.list_conversations()
        assert conversations == []

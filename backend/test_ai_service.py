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
        # Mock OpenAI response properly for the new SDK
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = 'Python is a programming language'
        mock_choice.message = mock_message
        mock_choice.finish_reason = 'stop'
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 50
        
        # Mock the new OpenAI SDK structure
        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        ai_service_instance.openai_client = mock_client
        
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

    def test_save_messages_with_model_tracking(self, ai_service_instance):
        """Test that _save_messages correctly tracks model information."""
        from db_models import ConversationDB, MessageDB
        from database import get_db_session
        
        # Create a test conversation
        with get_db_session() as db:
            conversation = ConversationDB(
                task="Test task",
                provider="openai",
                model="gpt-4",
                context_ids=[],
                prompt_type="full"
            )
            db.add(conversation)
            db.flush()  # Get the ID without committing
            conversation_id = conversation.id
        
        # Test messages with different roles
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!", "tokens": 10, "finish_reason": "stop"}
        ]
        
        # Save messages with model tracking
        ai_service_instance._save_messages(conversation_id, test_messages, "gpt-4")
        
        # Verify messages were saved with correct model tracking
        with get_db_session() as db:
            messages = db.query(MessageDB).filter(
                MessageDB.conversation_id == conversation_id
            ).order_by(MessageDB.created_at).all()
            
            assert len(messages) == 3
            
            # System message should not have model tracked
            system_msg = messages[0]
            assert system_msg.role == "system"
            assert system_msg.model is None
            
            # User message should not have model tracked
            user_msg = messages[1]
            assert user_msg.role == "user"
            assert user_msg.model is None
            
            # Assistant message should have model tracked
            assistant_msg = messages[2]
            assert assistant_msg.role == "assistant"
            assert assistant_msg.model == "gpt-4"
            assert assistant_msg.tokens == 10
            assert assistant_msg.finish_reason == "stop"

    def test_get_conversation_includes_model_info(self, ai_service_instance):
        """Test that get_conversation returns model info in messages."""
        from db_models import ConversationDB, MessageDB
        from database import get_db_session
        
        # Create test conversation and messages
        with get_db_session() as db:
            conversation = ConversationDB(
                task="Test conversation",
                provider="anthropic", 
                model="claude-3-sonnet-20240229",
                context_ids=[],
                prompt_type="full"
            )
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id
            
            # Add messages with model tracking
            messages = [
                MessageDB(
                    conversation_id=conversation_id,
                    role="user",
                    content="Test question",
                    model=None  # User messages don't track model
                ),
                MessageDB(
                    conversation_id=conversation_id,
                    role="assistant",
                    content="Test response",
                    tokens=25,
                    finish_reason="stop",
                    model="claude-3-sonnet-20240229"
                )
            ]
            db.add_all(messages)
        
        # Get conversation data
        conversation_data = ai_service_instance.get_conversation(conversation_id)
        
        assert conversation_data is not None
        assert len(conversation_data["messages"]) == 2
        
        # Check user message
        user_msg = conversation_data["messages"][0]
        assert user_msg["role"] == "user"
        assert user_msg["model"] is None
        
        # Check assistant message
        assistant_msg = conversation_data["messages"][1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["model"] == "claude-3-sonnet-20240229"
        assert assistant_msg["tokens"] == 25

    @patch('ai_service.openai')
    def test_openai_integration_saves_model(self, mock_openai, ai_service_instance, sample_prompt):
        """Test that OpenAI integration properly saves model information."""
        from database import get_db_session
        from db_models import MessageDB
        
        # Mock OpenAI client to be initialized
        mock_client = Mock()
        ai_service_instance.openai_client = mock_client
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 50
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Generate response
        response, conversation = ai_service_instance.generate_response(
            task="Test task",
            generated_prompt=sample_prompt,
            context_ids=[],
            provider="openai",
            model="gpt-4"
        )
        
        # Check that messages were saved with model info
        with get_db_session() as db:
            assistant_messages = db.query(MessageDB).filter(
                MessageDB.conversation_id == conversation.id,
                MessageDB.role == "assistant"
            ).all()
            
            assert len(assistant_messages) >= 1
            assert assistant_messages[0].model == "gpt-4"

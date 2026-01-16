"""
Tests for model switching within conversations.
Tests the fix for model attribution when changing models mid-conversation.
"""
import pytest
from ai_service import AIService
from composer import GeneratedPrompt
from db_models import ConversationDB, MessageDB
from database import get_db_session


class TestModelSwitching:
    """Test model switching functionality in conversations."""
    
    @pytest.fixture
    def ai_service_instance(self):
        """Create an AI service instance for testing."""
        return AIService()
    
    @pytest.fixture
    def sample_prompt(self):
        """Create a sample generated prompt."""
        return GeneratedPrompt(
            original_task="Test task",
            relevant_context=[],
            generated_prompt="Test prompt"
        )
    
    def test_model_switch_updates_conversation_model(self, ai_service_instance, sample_prompt, monkeypatch):
        """Test that switching models in a conversation updates the conversation model."""
        # Mock OpenAI client
        class MockOpenAI:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        class MockResponse:
                            class MockChoice:
                                class MockMessage:
                                    content = "Test response"
                                message = MockMessage()
                                finish_reason = "stop"
                            choices = [MockChoice()]
                            class MockUsage:
                                completion_tokens = 10
                                prompt_tokens = 5
                                total_tokens = 15
                            usage = MockUsage()
                            model = kwargs.get('model', 'gpt-4')
                        return MockResponse()
        
        monkeypatch.setattr(ai_service_instance, 'openai_client', MockOpenAI())
        
        # Create initial conversation with gpt-4
        _, conversation1 = ai_service_instance._generate_openai(
            task="First request",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            conversation_id=None
        )
        
        assert conversation1.model == "gpt-4"
        conversation_id = conversation1.id
        
        # Continue conversation with gpt-3.5-turbo
        _, conversation2 = ai_service_instance._generate_openai(
            task="Second request",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100,
            conversation_id=conversation_id
        )
        
        # Verify the conversation object reflects the new model
        assert conversation2.model == "gpt-3.5-turbo"
        assert conversation2.id == conversation_id  # Same conversation
    
    def test_model_switch_anthropic(self, ai_service_instance, sample_prompt, monkeypatch):
        """Test model switching with Anthropic provider."""
        # Mock Anthropic client
        class MockAnthropic:
            class messages:
                @staticmethod
                def create(**kwargs):
                    class MockResponse:
                        class MockContent:
                            text = "Test response"
                        content = [MockContent()]
                        stop_reason = "end_turn"
                        class MockUsage:
                            input_tokens = 5
                            output_tokens = 10
                        usage = MockUsage()
                        model = kwargs.get('model', 'claude-3-sonnet-20240229')
                    return MockResponse()
        
        monkeypatch.setattr(ai_service_instance, 'anthropic_client', MockAnthropic())
        
        # Create initial conversation with claude-3-sonnet
        _, conversation1 = ai_service_instance._generate_anthropic(
            task="First request",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=100,
            conversation_id=None
        )
        
        assert conversation1.model == "claude-3-sonnet-20240229"
        conversation_id = conversation1.id
        
        # Continue with claude-3-haiku
        _, conversation2 = ai_service_instance._generate_anthropic(
            task="Second request",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=100,
            conversation_id=conversation_id
        )
        
        # Verify model was updated
        assert conversation2.model == "claude-3-haiku-20240307"
        assert conversation2.id == conversation_id
    
    def test_model_remains_same_if_not_changed(self, ai_service_instance, sample_prompt, monkeypatch):
        """Test that model stays the same when not explicitly changed."""
        class MockOpenAI:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        class MockResponse:
                            class MockChoice:
                                class MockMessage:
                                    content = "Test response"
                                message = MockMessage()
                                finish_reason = "stop"
                            choices = [MockChoice()]
                            class MockUsage:
                                completion_tokens = 10
                                prompt_tokens = 5
                                total_tokens = 15
                            usage = MockUsage()
                            model = kwargs.get('model', 'gpt-4')
                        return MockResponse()
        
        monkeypatch.setattr(ai_service_instance, 'openai_client', MockOpenAI())
        
        # Create conversation
        _, conversation1 = ai_service_instance._generate_openai(
            task="First",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            conversation_id=None
        )
        
        conversation_id = conversation1.id
        
        # Continue with same model
        _, conversation2 = ai_service_instance._generate_openai(
            task="Second",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            conversation_id=conversation_id
        )
        
        # Model should remain unchanged
        assert conversation2.model == "gpt-4"
        assert conversation2.id == conversation_id
    
    def test_messages_track_individual_models(self, ai_service_instance, sample_prompt, monkeypatch):
        """Test that individual messages track which model generated them."""
        class MockOpenAI:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        class MockResponse:
                            class MockChoice:
                                class MockMessage:
                                    content = "Response"
                                message = MockMessage()
                                finish_reason = "stop"
                            choices = [MockChoice()]
                            class MockUsage:
                                completion_tokens = 10
                                prompt_tokens = 5
                                total_tokens = 15
                            usage = MockUsage()
                            model = kwargs.get('model', 'gpt-4')
                        return MockResponse()
        
        monkeypatch.setattr(ai_service_instance, 'openai_client', MockOpenAI())
        
        # First message with gpt-4
        _, conversation1 = ai_service_instance._generate_openai(
            task="First",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
            conversation_id=None
        )
        
        conversation_id = conversation1.id
        
        # Second message with gpt-3.5-turbo
        _, conversation2 = ai_service_instance._generate_openai(
            task="Second",
            generated_prompt=sample_prompt,
            context_ids=[],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100,
            conversation_id=conversation_id
        )
        
        # Get conversation and check messages
        conversation_data = ai_service_instance.get_conversation(conversation_id)
        assert conversation_data is not None
        
        messages = conversation_data['messages']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        
        # Should have 2 assistant messages with different models
        assert len(assistant_messages) == 2
        assert assistant_messages[0]['model'] == 'gpt-4'
        assert assistant_messages[1]['model'] == 'gpt-3.5-turbo'

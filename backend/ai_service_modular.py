"""
Modular AI Service using Provider System.

This is the next-generation AI service that uses the modular provider architecture.
Each LLM vendor has its own provider module with specific configuration and capabilities.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from config import settings
from logger import logger
from models import GeneratedPrompt
from db_models import ConversationDB, MessageDB
from database import get_db_session
from providers import ProviderRegistry, ProviderConfig, BaseLLMProvider


class ModularAIService:
    """
    AI service that uses modular provider architecture.
    
    This service manages LLM providers as pluggable modules, making it easy to:
    - Add new LLM providers without modifying the core service
    - Configure each provider with its specific settings
    - Switch between providers seamlessly
    - Support multiple active providers simultaneously
    """
    
    def __init__(self):
        """Initialize the modular AI service."""
        self.registry = ProviderRegistry()
        self.active_providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers_from_config()
    
    def _initialize_providers_from_config(self):
        """Initialize providers based on application configuration."""
        logger.info("Initializing providers from configuration...")
        
        # Initialize OpenAI if API key is available
        if settings.openai_api_key:
            try:
                config = ProviderConfig(
                    provider_name="openai",
                    display_name="OpenAI",
                    api_key=settings.openai_api_key,
                    default_model=settings.default_ai_model if settings.default_ai_provider == "openai" else "gpt-4o",
                    default_temperature=settings.ai_temperature,
                    default_max_tokens=settings.ai_max_tokens
                )
                provider = self.registry.get_provider("openai", config)
                self.active_providers["openai"] = provider
                logger.info("✓ OpenAI provider initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize OpenAI provider: {e}")
        
        # Initialize Anthropic if API key is available
        if settings.anthropic_api_key:
            try:
                config = ProviderConfig(
                    provider_name="anthropic",
                    display_name="Anthropic",
                    api_key=settings.anthropic_api_key,
                    default_model=settings.default_ai_model if settings.default_ai_provider == "anthropic" else "claude-3-7-sonnet-20250219",
                    default_temperature=settings.ai_temperature,
                    default_max_tokens=settings.ai_max_tokens
                )
                provider = self.registry.get_provider("anthropic", config)
                self.active_providers["anthropic"] = provider
                logger.info("✓ Anthropic provider initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Anthropic provider: {e}")
        
        # Initialize Ollama if base URL is configured
        if settings.ollama_base_url:
            try:
                config = ProviderConfig(
                    provider_name="ollama",
                    display_name="Ollama",
                    base_url=settings.ollama_base_url,
                    api_key=settings.ollama_api_key,
                    default_model=settings.default_ai_model if settings.default_ai_provider == "ollama" else "llama3.2",
                    default_temperature=settings.ai_temperature,
                    default_max_tokens=settings.ai_max_tokens
                )
                provider = self.registry.get_provider("ollama", config)
                self.active_providers["ollama"] = provider
                logger.info("✓ Ollama provider initialized")
            except Exception as e:
                logger.error(f"✗ Failed to initialize Ollama provider: {e}")
        
        logger.info(f"Initialized {len(self.active_providers)} provider(s): {', '.join(self.active_providers.keys())}")
    
    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Get an active provider by name.
        
        Args:
            provider_name: Name of the provider
        
        Returns:
            Provider instance
        
        Raises:
            ValueError: If provider not found or not initialized
        """
        if provider_name not in self.active_providers:
            available = ", ".join(self.active_providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not initialized or not available. "
                f"Active providers: {available}"
            )
        return self.active_providers[provider_name]
    
    def generate_response(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, ConversationDB]:
        """
        Generate AI response using the specified provider.
        
        Args:
            task: User's original task
            generated_prompt: The contextualized prompt
            context_ids: List of context IDs used
            provider: AI provider name (e.g., "openai", "anthropic", "ollama")
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Max tokens in response
            conversation_id: Optional ID of existing conversation to continue
        
        Returns:
            Tuple of (response_text, conversation_record)
        """
        # Use default provider if none specified
        provider = provider or settings.default_ai_provider
        
        # Get the provider instance
        try:
            provider_instance = self.get_provider(provider)
        except ValueError as e:
            raise ValueError(f"Cannot generate response: {e}")
        
        # Get existing conversation if continuing
        existing_conversation = None
        conversation_messages = []
        
        if conversation_id:
            conversation_data = self.get_conversation(conversation_id)
            if conversation_data:
                existing_conversation = conversation_data
                # Extract messages in standard format
                for msg in conversation_data['messages']:
                    if msg['role'] in ['user', 'assistant', 'system']:
                        conversation_messages.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })
        
        # Prepare messages for this provider
        messages = provider_instance.prepare_messages(
            prompt=generated_prompt,
            conversation_messages=conversation_messages if conversation_messages else None
        )
        
        # Create or update conversation record
        if existing_conversation:
            current_conversation_id = existing_conversation['id']
            conversation = self._get_conversation_object(current_conversation_id)
            # Update model if different
            if conversation and model and conversation.model != model:
                conversation.model = model
        else:
            conversation = self._create_conversation(
                task=task,
                prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                context_ids=context_ids,
                provider=provider,
                model=model or provider_instance.config.default_model
            )
            current_conversation_id = conversation.id
        
        # Generate response using the provider
        try:
            response_text, metadata = provider_instance.generate_response(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Save messages to database
            new_messages = [
                {
                    "role": "user",
                    "content": generated_prompt.generated_prompt
                },
                {
                    "role": "assistant",
                    "content": response_text,
                    "tokens": metadata.get("tokens_used", 0),
                    "finish_reason": metadata.get("finish_reason", ""),
                    "model": metadata.get("model_used", model)
                }
            ]
            
            # Add system message if this is a new conversation and provider supports it
            if not existing_conversation and provider_instance.config.capabilities.supports_system_messages:
                new_messages.insert(0, {
                    "role": "system",
                    "content": "You are a helpful AI assistant with access to personalized context."
                })
            
            self._save_messages(current_conversation_id, new_messages)
            
            logger.info(
                f"Response generated via {provider} provider: "
                f"{metadata.get('model_used', model)}, "
                f"{metadata.get('tokens_used', 0)} tokens"
            )
            
            return response_text, conversation
        
        except Exception as e:
            logger.error(f"Error generating response with {provider}: {e}")
            raise
    
    def list_available_models(self, provider: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        List available models for all or specific provider(s).
        
        Args:
            provider: Optional provider name to filter by
        
        Returns:
            Dict mapping provider names to their available models
        """
        results = {}
        
        if provider:
            # Get models for specific provider
            if provider in self.active_providers:
                provider_instance = self.active_providers[provider]
                results[provider] = provider_instance.list_available_models()
        else:
            # Get models for all active providers
            for provider_name, provider_instance in self.active_providers.items():
                try:
                    models = provider_instance.list_available_models()
                    results[provider_name] = models
                except Exception as e:
                    logger.warning(f"Could not list models for {provider_name}: {e}")
                    results[provider_name] = []
        
        return results
    
    def get_provider_info(self) -> List[Dict]:
        """
        Get information about all active providers.
        
        Returns:
            List of provider info dicts
        """
        info = []
        for name, provider in self.active_providers.items():
            capabilities = provider.get_capabilities()
            is_healthy, health_message = provider.health_check()
            
            info.append({
                "name": name,
                "display_name": provider.config.display_name,
                "initialized": provider.is_initialized(),
                "healthy": is_healthy,
                "health_message": health_message,
                "default_model": provider.config.default_model,
                "capabilities": {
                    "streaming": capabilities.supports_streaming,
                    "function_calling": capabilities.supports_function_calling,
                    "vision": capabilities.supports_vision,
                    "system_messages": capabilities.supports_system_messages,
                    "temperature": capabilities.supports_temperature,
                    "local_inference": capabilities.custom_features.get("local_inference", False),
                    "auto_pull_models": capabilities.custom_features.get("auto_pull_models", False),
                }
            })
        
        return info
    
    # Database helper methods (same as original AIService)
    
    def _create_conversation(
        self,
        task: str,
        prompt_type: str,
        context_ids: List[str],
        provider: str,
        model: str
    ) -> ConversationDB:
        """Create a conversation record in the database."""
        with get_db_session() as db:
            conversation = ConversationDB(
                task=task,
                prompt_type=prompt_type,
                provider=provider,
                model=model,
                context_ids=context_ids
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            conversation_id = conversation.id
            conversation_data = {
                "id": conversation.id,
                "task": conversation.task,
                "prompt_type": conversation.prompt_type,
                "provider": conversation.provider,
                "model": conversation.model,
                "context_ids": conversation.context_ids,
                "created_at": conversation.created_at
            }
            
            detached_conversation = ConversationDB(**conversation_data)
            detached_conversation.id = conversation_id
            return detached_conversation
    
    def _save_messages(self, conversation_id: str, messages: List[Dict]):
        """Save messages to the database."""
        with get_db_session() as db:
            for msg in messages:
                db_message = MessageDB(
                    conversation_id=conversation_id,
                    role=msg["role"],
                    content=msg["content"],
                    tokens=msg.get("tokens"),
                    finish_reason=msg.get("finish_reason"),
                    model=msg.get("model") if msg["role"] == "assistant" else None
                )
                db.add(db_message)
    
    def _get_conversation_object(self, conversation_id: str) -> Optional[ConversationDB]:
        """Get a conversation object for return compatibility."""
        with get_db_session() as db:
            conversation = db.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()
            if conversation:
                conv_copy = ConversationDB(
                    id=conversation.id,
                    task=conversation.task,
                    prompt_type=conversation.prompt_type,
                    provider=conversation.provider,
                    model=conversation.model,
                    context_ids=conversation.context_ids,
                    created_at=conversation.created_at
                )
                return conv_copy
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation with all its messages."""
        with get_db_session() as db:
            conversation = db.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()
            
            if not conversation:
                return None
            
            return {
                "id": conversation.id,
                "task": conversation.task,
                "prompt_type": conversation.prompt_type,
                "provider": conversation.provider,
                "model": conversation.model,
                "context_ids": conversation.context_ids,
                "created_at": conversation.created_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "tokens": msg.tokens,
                        "finish_reason": msg.finish_reason,
                        "model": msg.model,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in conversation.messages
                ]
            }
    
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List recent conversations."""
        with get_db_session() as db:
            conversations = db.query(ConversationDB)\
                .order_by(ConversationDB.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return [
                {
                    "id": conv.id,
                    "task": conv.task,
                    "prompt_type": conv.prompt_type,
                    "provider": conv.provider,
                    "model": conv.model,
                    "created_at": conv.created_at.isoformat(),
                    "message_count": len(conv.messages)
                }
                for conv in conversations
            ]


# Create global instance
modular_ai_service = ModularAIService()

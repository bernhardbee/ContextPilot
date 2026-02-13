"""
AI service integration for OpenAI and Anthropic.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import subprocess
import time
import openai
from openai import OpenAI, APIConnectionError, APIStatusError
from anthropic import Anthropic

from config import settings
from logger import logger
from models import GeneratedPrompt
from db_models import ConversationDB, MessageDB
from database import get_db_session
from validators import validate_ai_model


class AIService:
    """
    Unified AI service for multiple providers.
    """
    
    def __init__(self):
        """Initialize AI service with configured providers."""
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_client = None
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
        
        # Ollama uses OpenAI-compatible API
        if settings.ollama_base_url:
            from openai import OpenAI
            self.ollama_client = OpenAI(
                base_url=f"{settings.ollama_base_url}/v1",
                api_key=settings.ollama_api_key  # Usually not required but needed for API compatibility
            )
            logger.info(f"Ollama client initialized at {settings.ollama_base_url}")
    
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
        
        Note: This is a synchronous method as it makes blocking API calls.
        Consider using async httpx client for true async in the future.
        
        Args:
            task: User's original task
            generated_prompt: The contextualized prompt
            context_ids: List of context IDs used
            provider: AI provider ("openai" or "anthropic")
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Max tokens in response
            conversation_id: Optional ID of existing conversation to continue
            
        Returns:
            Tuple of (response_text, conversation_record)
        """
        provider = provider or settings.default_ai_provider
        model = model or settings.default_ai_model
        
        # Validate model for the provider
        if provider != "ollama":  # Skip validation for Ollama as models are dynamic
            validate_ai_model(provider, model)
        temperature = temperature if temperature is not None else settings.ai_temperature
        max_tokens = max_tokens or settings.ai_max_tokens
        
        if provider == "openai":
            return self._generate_openai(
                task, generated_prompt, context_ids, model, temperature, max_tokens, conversation_id
            )
        elif provider == "anthropic":
            return self._generate_anthropic(
                task, generated_prompt, context_ids, model, temperature, max_tokens, conversation_id
            )
        elif provider == "ollama":
            return self._generate_ollama(
                task, generated_prompt, context_ids, model, temperature, max_tokens, conversation_id
            )
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    def _generate_openai(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        model: str,
        temperature: float,
        max_tokens: int,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, ConversationDB]:
        """Generate response using OpenAI API (synchronous)."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Get existing conversation and its messages if continuing
            existing_conversation = None
            existing_messages = []
            if conversation_id:
                conversation_data = self.get_conversation(conversation_id)
                if conversation_data:
                    existing_conversation = conversation_data
                    # Convert stored messages to API format (excluding system messages for continuation)
                    for msg in conversation_data['messages']:
                        if msg['role'] in ['user', 'assistant']:
                            existing_messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })

            # Create or get existing conversation record
            if existing_conversation:
                # Use the existing conversation ID to save new messages
                current_conversation_id = existing_conversation['id']
                # Create a temporary conversation object for return compatibility
                conversation = self._get_conversation_object(current_conversation_id)
                # Update conversation model if different from requested model
                if conversation and conversation.model != model:
                    conversation.model = model
            else:
                conversation = self._create_conversation(
                    task=task,
                    prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                    context_ids=context_ids,
                    provider="openai",
                    model=model
                )
                current_conversation_id = conversation.id
            
            # Prepare messages - start with system message
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."}
            ]
            
            # Add existing conversation history
            messages.extend(existing_messages)
            
            # Add current user message (contextualized prompt)
            messages.append({"role": "user", "content": generated_prompt.generated_prompt})
            
            # Call OpenAI API (v1.0+ syntax)
            # Handle model-specific parameter support
            api_params = {
                "model": model,
                "messages": messages,
            }
            
            # Handle token parameter based on model type
            # O-series models (o1, o3, o1-mini, o3-mini) use max_completion_tokens
            if model.startswith(('o1', 'o3')):
                api_params["max_completion_tokens"] = max_tokens
            else:
                api_params["max_tokens"] = max_tokens
            
            # O-series models don't support temperature parameter
            if not model.startswith(('o1', 'o3')):
                api_params["temperature"] = temperature
                
            response = self.openai_client.chat.completions.create(**api_params)
            
            # Extract response
            assistant_message = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens
            
            # Log warning if content is empty
            if not assistant_message:
                logger.warning(f"Empty response from OpenAI. Finish reason: {finish_reason}, Tokens: {tokens_used}")
            
            # Save new messages (only the new user and assistant messages)
            new_messages = [
                {"role": "user", "content": generated_prompt.generated_prompt},
                {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
            ]
            
            # If this is a new conversation, also save the system message
            if not existing_conversation:
                new_messages.insert(0, {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."})
            
            self._save_messages(current_conversation_id, new_messages, model)
            
            logger.info(f"OpenAI response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_anthropic(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        model: str,
        temperature: float,
        max_tokens: int,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, ConversationDB]:
        """Generate response using Anthropic API (synchronous)."""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            # Get existing conversation and its messages if continuing
            existing_conversation = None
            existing_messages = []
            if conversation_id:
                conversation_data = self.get_conversation(conversation_id)
                if conversation_data:
                    existing_conversation = conversation_data
                    # Convert stored messages to API format (exclude system messages for Anthropic)
                    for msg in conversation_data['messages']:
                        if msg['role'] in ['user', 'assistant']:
                            existing_messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })

            # Create or get existing conversation record
            if existing_conversation:
                # Use the existing conversation ID to save new messages
                current_conversation_id = existing_conversation['id']
                # Create a temporary conversation object for return compatibility
                conversation = self._get_conversation_object(current_conversation_id)
                # Update conversation model if different from requested model
                if conversation and conversation.model != model:
                    conversation.model = model
            else:
                conversation = self._create_conversation(
                    task=task,
                    prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                    context_ids=context_ids,
                    provider="anthropic",
                    model=model
                )
                current_conversation_id = conversation.id
            
            # Prepare messages - Anthropic doesn't use system messages in the same way
            messages = existing_messages.copy()
            messages.append({"role": "user", "content": generated_prompt.generated_prompt})
            
            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            # Extract response
            assistant_message = response.content[0].text
            finish_reason = response.stop_reason
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Save new messages (only the new user and assistant messages)
            new_messages = [
                {"role": "user", "content": generated_prompt.generated_prompt},
                {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
            ]
            
            self._save_messages(current_conversation_id, new_messages, model)
            
            logger.info(f"Anthropic response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _check_ollama_model_exists(self, model: str) -> bool:
        """Check if an Ollama model is already pulled/installed."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Check if model name appears in the output
                return model in result.stdout
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not check Ollama models: {e}")
            return False
    
    def _pull_ollama_model(self, model: str) -> bool:
        """
        Pull an Ollama model automatically.
        Returns True if successful, False otherwise.
        """
        try:
            logger.info(f"Pulling Ollama model '{model}'... This may take a few minutes.")
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout for large models
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled Ollama model '{model}'")
                return True
            else:
                logger.error(f"Failed to pull Ollama model '{model}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while pulling Ollama model '{model}' (exceeded 10 minutes)")
            return False
        except FileNotFoundError:
            logger.error("Ollama CLI not found. Is Ollama installed?")
            return False
        except Exception as e:
            logger.error(f"Error pulling Ollama model '{model}': {e}")
            return False
    
    def _generate_ollama(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        model: str,
        temperature: float,
        max_tokens: int,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, ConversationDB]:
        """Generate response using Ollama (OpenAI-compatible API)."""
        if not self.ollama_client:
            raise ValueError("Ollama not configured. Set CONTEXTPILOT_OLLAMA_BASE_URL environment variable.")
        
        try:
            # Get existing conversation and its messages if continuing
            existing_conversation = None
            existing_messages = []
            if conversation_id:
                conversation_data = self.get_conversation(conversation_id)
                if conversation_data:
                    existing_conversation = conversation_data
                    # Convert stored messages to API format
                    for msg in conversation_data['messages']:
                        if msg['role'] in ['user', 'assistant', 'system']:
                            existing_messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })

            # Create or get existing conversation record
            if existing_conversation:
                current_conversation_id = existing_conversation['id']
                conversation = self._get_conversation_object(current_conversation_id)
                # Update conversation model if different from requested model
                if conversation and conversation.model != model:
                    conversation.model = model
            else:
                conversation = self._create_conversation(
                    task=task,
                    prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                    context_ids=context_ids,
                    provider="ollama",
                    model=model
                )
                current_conversation_id = conversation.id
            
            # Prepare messages for Ollama
            if not existing_messages:
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."}
                ]
            else:
                messages = existing_messages.copy()
            
            messages.append({"role": "user", "content": generated_prompt.generated_prompt})
            
            # Call Ollama API (OpenAI-compatible)
            response = self.ollama_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            
            # Log warning if content is empty
            if not assistant_message:
                logger.warning(f"Empty response from Ollama. Finish reason: {finish_reason}, Tokens: {tokens_used}")
            
            # Save new messages
            new_messages = [
                {"role": "user", "content": generated_prompt.generated_prompt},
                {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
            ]
            
            # If this is a new conversation, also save the system message
            if not existing_conversation:
                new_messages.insert(0, {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."})
            
            self._save_messages(current_conversation_id, new_messages, model)
            
            logger.info(f"Ollama response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except APIConnectionError as e:
            # Connection errors - Ollama not running or unreachable
            logger.error(f"Cannot connect to Ollama at {self.ollama_client.base_url}: {e}")
            raise ValueError(
                f"Cannot connect to Ollama server at {self.ollama_client.base_url}. "
                "Please ensure Ollama is installed and running. "
                "Install: https://ollama.ai | Start: 'ollama serve'"
            )
        except APIStatusError as e:
            # API errors - model not found, etc.
            if e.status_code == 404:
                logger.info(f"Ollama model '{model}' not found, attempting to pull it automatically...")
                
                # Try to pull the model automatically
                pull_success = self._pull_ollama_model(model)
                
                if pull_success:
                    # Retry the request with the newly pulled model
                    logger.info(f"Model '{model}' pulled successfully, retrying request...")
                    # Wait a moment for Ollama to register the model
                    time.sleep(2)
                    
                    try:
                        # Retry the API call
                        response = self.ollama_client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        # Extract response
                        assistant_message = response.choices[0].message.content or ""
                        finish_reason = response.choices[0].finish_reason
                        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                        
                        if not assistant_message:
                            logger.warning(f"Empty response from Ollama. Finish reason: {finish_reason}, Tokens: {tokens_used}")
                        
                        # Save messages
                        new_messages = [
                            {"role": "user", "content": generated_prompt.generated_prompt},
                            {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
                        ]
                        
                        if not existing_conversation:
                            new_messages.insert(0, {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."})
                        
                        self._save_messages(current_conversation_id, new_messages, model)
                        
                        logger.info(f"Ollama response generated after auto-pull: {model}, {tokens_used} tokens")
                        return assistant_message, conversation
                        
                    except Exception as retry_error:
                        logger.error(f"Failed to generate response after pulling model: {retry_error}")
                        raise ValueError(f"Model '{model}' was pulled but failed to generate response: {retry_error}")
                else:
                    # Pull failed
                    raise ValueError(
                        f"Model '{model}' not found and automatic download failed. "
                        f"Please pull it manually: ollama pull {model}"
                    )
            else:
                logger.error(f"Ollama API error ({e.status_code}): {e}")
                raise ValueError(f"Ollama API error: {e.message if hasattr(e, 'message') else str(e)}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected Ollama error: {error_msg}")
            raise ValueError(f"Ollama error: {error_msg}")
    
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
            
            # Make the conversation accessible outside the session
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
            
            # Create a detached conversation object with the same data
            detached_conversation = ConversationDB(**conversation_data)
            detached_conversation.id = conversation_id
            return detached_conversation
    
    def _save_messages(self, conversation_id: str, messages: List[Dict], model: str = None):
        """Save messages to the database."""
        with get_db_session() as db:
            for msg in messages:
                db_message = MessageDB(
                    conversation_id=conversation_id,
                    role=msg["role"],
                    content=msg["content"],
                    tokens=msg.get("tokens"),
                    finish_reason=msg.get("finish_reason"),
                    model=model if msg["role"] == "assistant" else None  # Only track model for assistant responses
                )
                db.add(db_message)
            # Commit handled by context manager
    
    def _get_conversation_object(self, conversation_id: str) -> Optional[ConversationDB]:
        """Get a conversation object for return compatibility."""
        with get_db_session() as db:
            conversation = db.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()
            if conversation:
                # Create a detached copy to avoid session issues
                from copy import copy
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


# Global AI service instance
ai_service = AIService()

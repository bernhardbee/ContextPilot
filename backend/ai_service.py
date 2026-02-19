"""
AI service integration for OpenAI and Anthropic.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import subprocess
import time
import openai
from openai import OpenAI, APIConnectionError, APIStatusError
from anthropic import Anthropic, APIConnectionError as AnthropicAPIConnectionError, APIStatusError as AnthropicAPIStatusError

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
            if settings.openai_base_url:
                self.openai_client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url
                )
                logger.info(f"OpenAI client initialized with base URL: {settings.openai_base_url}")
            else:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized")
        
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
        
        # Ollama uses OpenAI-compatible API
        if settings.ollama_base_url:
            self.ollama_client = OpenAI(
                base_url=f"{settings.ollama_base_url}/v1",
                api_key=settings.ollama_api_key  # Usually not required but needed for API compatibility
            )
            logger.info(f"Ollama client initialized at {settings.ollama_base_url}")

    def _resolve_model_name(self, candidate: object, fallback: str) -> str:
        """Return a safe, string model name for persistence and attribution."""
        return candidate if isinstance(candidate, str) and candidate else fallback

    def _format_openai_status_error(self, status_code: int, model: Optional[str], raw_message: str) -> str:
        """Build user-facing OpenAI status error messages."""
        if status_code in (401, 403):
            return "OpenAI authentication failed. The configured API key was rejected. Please verify the key in Settings → OpenAI."
        if status_code == 404:
            if model:
                return f"OpenAI model '{model}' was not found for this account or endpoint. Select a valid OpenAI model in Settings."
            return "OpenAI resource was not found. Check your configured base URL and selected model."
        if status_code == 429:
            return "OpenAI rate limit or quota exceeded. Please check usage limits and billing on your OpenAI account."
        return f"OpenAI request failed ({status_code}): {raw_message}"

    def _format_anthropic_status_error(self, status_code: int, model: Optional[str], raw_message: str) -> str:
        """Build user-facing Anthropic status error messages."""
        if status_code in (401, 403):
            return "Anthropic authentication failed. The configured API key was rejected. Please verify the key in Settings → Anthropic."
        if status_code == 404:
            if model:
                return f"Anthropic model '{model}' was not found or is unavailable for this account. Select a valid Claude model in Settings."
            return "Anthropic resource was not found. Check the selected model in Settings."
        if status_code == 429:
            return "Anthropic rate limit or quota exceeded. Please check your Anthropic usage limits and billing."
        return f"Anthropic request failed ({status_code}): {raw_message}"

    def _uses_openai_completion_tokens(self, model: str) -> bool:
        """Return True when model expects `max_completion_tokens` instead of `max_tokens`.

        OpenAI o-series and GPT-5 family models reject legacy `max_tokens`.
        """
        return model.startswith(("o1", "o3", "gpt-5"))

    def _is_max_tokens_unsupported_error(self, status_code: int, message: str) -> bool:
        """Detect OpenAI errors that indicate `max_tokens` is unsupported for selected model."""
        text = (message or "").lower()
        return (
            status_code == 400
            and "max_tokens" in text
            and "max_completion_tokens" in text
            and "unsupported" in text
        )

    def validate_provider_connection(self, provider: str, model: Optional[str] = None) -> Dict[str, object]:
        """Validate that configured provider credentials and connectivity are usable."""
        provider_name = (provider or "").strip().lower()
        if provider_name not in {"openai", "anthropic", "ollama"}:
            raise ValueError(f"Unsupported provider '{provider}'.")

        if provider_name == "openai":
            if not settings.openai_api_key or not self.openai_client:
                return {
                    "provider": "openai",
                    "valid": False,
                    "message": "OpenAI API key is not configured.",
                    "checked_model": model or settings.openai_default_model or settings.default_ai_model,
                }

            try:
                self.openai_client.models.list()
                return {
                    "provider": "openai",
                    "valid": True,
                    "message": "OpenAI connection and API key are valid.",
                    "checked_model": model or settings.openai_default_model or settings.default_ai_model,
                }
            except APIConnectionError as e:
                return {
                    "provider": "openai",
                    "valid": False,
                    "message": f"Cannot connect to OpenAI API. Check network and base URL. Details: {e}",
                    "checked_model": model or settings.openai_default_model or settings.default_ai_model,
                }
            except APIStatusError as e:
                status_code = int(getattr(e, "status_code", 0) or 0)
                message = getattr(e, "message", None) or str(e)
                return {
                    "provider": "openai",
                    "valid": False,
                    "message": self._format_openai_status_error(status_code, model, message),
                    "checked_model": model or settings.openai_default_model or settings.default_ai_model,
                }
            except Exception as e:
                return {
                    "provider": "openai",
                    "valid": False,
                    "message": f"OpenAI validation failed: {e}",
                    "checked_model": model or settings.openai_default_model or settings.default_ai_model,
                }

        if provider_name == "anthropic":
            checked_model = model or settings.anthropic_default_model or settings.default_ai_model
            if not settings.anthropic_api_key or not self.anthropic_client:
                return {
                    "provider": "anthropic",
                    "valid": False,
                    "message": "Anthropic API key is not configured.",
                    "checked_model": checked_model,
                }

            try:
                self.anthropic_client.messages.create(
                    model=checked_model,
                    max_tokens=1,
                    temperature=0,
                    messages=[{"role": "user", "content": "ping"}],
                )
                return {
                    "provider": "anthropic",
                    "valid": True,
                    "message": "Anthropic connection and API key are valid.",
                    "checked_model": checked_model,
                }
            except AnthropicAPIConnectionError as e:
                return {
                    "provider": "anthropic",
                    "valid": False,
                    "message": f"Cannot connect to Anthropic API. Check network connectivity. Details: {e}",
                    "checked_model": checked_model,
                }
            except AnthropicAPIStatusError as e:
                status_code = int(getattr(e, "status_code", 0) or 0)
                message = str(e)
                return {
                    "provider": "anthropic",
                    "valid": False,
                    "message": self._format_anthropic_status_error(status_code, checked_model, message),
                    "checked_model": checked_model,
                }
            except Exception as e:
                return {
                    "provider": "anthropic",
                    "valid": False,
                    "message": f"Anthropic validation failed: {e}",
                    "checked_model": checked_model,
                }

        checked_model = model or settings.ollama_default_model or settings.default_ai_model
        if not self.ollama_client:
            return {
                "provider": "ollama",
                "valid": False,
                "message": "Ollama is not configured. Set Ollama base URL in Settings.",
                "checked_model": checked_model,
            }

        try:
            self.ollama_client.models.list()
            return {
                "provider": "ollama",
                "valid": True,
                "message": "Ollama server is reachable.",
                "checked_model": checked_model,
            }
        except APIConnectionError as e:
            return {
                "provider": "ollama",
                "valid": False,
                "message": f"Cannot connect to Ollama server. Ensure Ollama is running. Details: {e}",
                "checked_model": checked_model,
            }
        except Exception as e:
            return {
                "provider": "ollama",
                "valid": False,
                "message": f"Ollama validation failed: {e}",
                "checked_model": checked_model,
            }
    
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
        if model is None:
            if provider == "openai" and settings.openai_default_model:
                model = settings.openai_default_model
            elif provider == "anthropic" and settings.anthropic_default_model:
                model = settings.anthropic_default_model
            elif provider == "ollama" and settings.ollama_default_model:
                model = settings.ollama_default_model
            else:
                model = settings.default_ai_model
        
        # Fail fast on missing provider configuration
        if provider == "openai" and not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        if provider == "anthropic" and not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        if provider == "ollama" and not self.ollama_client:
            raise ValueError("Ollama not configured. Set CONTEXTPILOT_OLLAMA_BASE_URL environment variable.")

        # Validate model for the provider
        if provider != "ollama":  # Skip validation for Ollama as models are dynamic
            validate_ai_model(provider, model)
        if temperature is None:
            if provider == "openai" and settings.openai_temperature is not None:
                temperature = settings.openai_temperature
            elif provider == "anthropic" and settings.anthropic_temperature is not None:
                temperature = settings.anthropic_temperature
            elif provider == "ollama" and settings.ollama_temperature is not None:
                temperature = settings.ollama_temperature
            else:
                temperature = settings.ai_temperature
        if max_tokens is None:
            if provider == "openai" and settings.openai_max_tokens is not None:
                max_tokens = settings.openai_max_tokens
            elif provider == "anthropic" and settings.anthropic_max_tokens is not None:
                max_tokens = settings.anthropic_max_tokens
            elif provider == "ollama" and settings.ollama_num_predict is not None:
                max_tokens = settings.ollama_num_predict
            else:
                max_tokens = settings.ai_max_tokens
        
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
                # Keep conversation metadata aligned with the provider/model in use
                if conversation and (conversation.provider != "openai" or conversation.model != model):
                    self._update_conversation_metadata(current_conversation_id, "openai", model)
                    conversation.provider = "openai"
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
            
            # Handle token parameter based on model family
            # O-series and GPT-5 models use max_completion_tokens
            if self._uses_openai_completion_tokens(model):
                api_params["max_completion_tokens"] = max_tokens
            else:
                api_params["max_tokens"] = max_tokens
            
            # O-series models don't support temperature parameter
            if not self._uses_openai_completion_tokens(model):
                api_params["temperature"] = temperature
            if settings.openai_top_p is not None:
                api_params["top_p"] = settings.openai_top_p

            try:
                response = self.openai_client.chat.completions.create(**api_params)
            except APIStatusError as e:
                status_code = int(getattr(e, "status_code", 0) or 0)
                message = getattr(e, "message", None) or str(e)
                if "max_tokens" in api_params and self._is_max_tokens_unsupported_error(status_code, message):
                    logger.warning(
                        f"OpenAI model '{model}' rejected max_tokens; retrying with max_completion_tokens"
                    )
                    retry_params = dict(api_params)
                    retry_params.pop("max_tokens", None)
                    retry_params["max_completion_tokens"] = max_tokens
                    response = self.openai_client.chat.completions.create(**retry_params)
                else:
                    raise
            
            # Extract response
            assistant_message = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens
            actual_model = self._resolve_model_name(getattr(response, "model", None), model)

            # Persist the actual provider/model that generated this response
            self._update_conversation_metadata(current_conversation_id, "openai", actual_model)
            conversation.provider = "openai"
            conversation.model = actual_model
            
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
            
            self._save_messages(current_conversation_id, new_messages, actual_model)
            
            logger.info(f"OpenAI response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise ValueError(
                "Cannot connect to OpenAI API. Check your network or OpenAI base URL configuration."
            )
        except APIStatusError as e:
            status_code = int(getattr(e, "status_code", 0) or 0)
            message = getattr(e, "message", None) or str(e)
            logger.error(f"OpenAI API status error ({status_code}): {message}")
            raise ValueError(self._format_openai_status_error(status_code, model, message))
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
                # Keep conversation metadata aligned with the provider/model in use
                if conversation and (conversation.provider != "anthropic" or conversation.model != model):
                    self._update_conversation_metadata(current_conversation_id, "anthropic", model)
                    conversation.provider = "anthropic"
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
            anthropic_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            if settings.anthropic_top_p is not None:
                anthropic_params["top_p"] = settings.anthropic_top_p
            if settings.anthropic_top_k is not None:
                anthropic_params["top_k"] = settings.anthropic_top_k
            response = self.anthropic_client.messages.create(**anthropic_params)
            
            # Extract response
            assistant_message = response.content[0].text
            finish_reason = response.stop_reason
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            actual_model = self._resolve_model_name(getattr(response, "model", None), model)

            # Persist the actual provider/model that generated this response
            self._update_conversation_metadata(current_conversation_id, "anthropic", actual_model)
            conversation.provider = "anthropic"
            conversation.model = actual_model
            
            # Save new messages (only the new user and assistant messages)
            new_messages = [
                {"role": "user", "content": generated_prompt.generated_prompt},
                {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
            ]
            
            self._save_messages(current_conversation_id, new_messages, actual_model)
            
            logger.info(f"Anthropic response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except AnthropicAPIConnectionError as e:
            logger.error(f"Anthropic connection error: {e}")
            raise ValueError("Cannot connect to Anthropic API. Check your network connectivity.")
        except AnthropicAPIStatusError as e:
            status_code = int(getattr(e, "status_code", 0) or 0)
            message = str(e)
            logger.error(f"Anthropic API status error ({status_code}): {message}")
            raise ValueError(self._format_anthropic_status_error(status_code, model, message))
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
                # Keep conversation metadata aligned with the provider/model in use
                if conversation and (conversation.provider != "ollama" or conversation.model != model):
                    self._update_conversation_metadata(current_conversation_id, "ollama", model)
                    conversation.provider = "ollama"
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
            actual_model = self._resolve_model_name(getattr(response, "model", None), model)

            # Persist the actual provider/model that generated this response
            self._update_conversation_metadata(current_conversation_id, "ollama", actual_model)
            conversation.provider = "ollama"
            conversation.model = actual_model
            
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
            
            self._save_messages(current_conversation_id, new_messages, actual_model)
            
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
                        actual_model = self._resolve_model_name(getattr(response, "model", None), model)

                        # Persist the actual provider/model that generated this response
                        self._update_conversation_metadata(current_conversation_id, "ollama", actual_model)
                        conversation.provider = "ollama"
                        conversation.model = actual_model
                        
                        if not assistant_message:
                            logger.warning(f"Empty response from Ollama. Finish reason: {finish_reason}, Tokens: {tokens_used}")
                        
                        # Save messages
                        new_messages = [
                            {"role": "user", "content": generated_prompt.generated_prompt},
                            {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
                        ]
                        
                        if not existing_conversation:
                            new_messages.insert(0, {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."})
                        
                        self._save_messages(current_conversation_id, new_messages, actual_model)
                        
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

    def _update_conversation_metadata(self, conversation_id: str, provider: str, model: str):
        """Persist provider/model metadata for an existing conversation."""
        with get_db_session() as db:
            conversation = db.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()
            if conversation:
                conversation.provider = provider
                conversation.model = model
    
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

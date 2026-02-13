"""
Ollama LLM Provider Integration.

This module provides integration with Ollama for running local LLMs.
Ollama uses an OpenAI-compatible API but has unique features like automatic model pulling.
"""
from typing import List, Dict, Optional, Tuple, Any
import subprocess
import time
from openai import OpenAI, APIConnectionError, APIStatusError

from .base_provider import BaseLLMProvider, ProviderConfig, ProviderCapabilities
from logger import logger


class OllamaProvider(BaseLLMProvider):
    """Ollama provider implementation for local LLM inference."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize Ollama provider with configuration."""
        # Set Ollama-specific capabilities
        if not config.capabilities:
            config.capabilities = ProviderCapabilities(
                supports_streaming=True,
                supports_function_calling=False,  # Most Ollama models don't support this
                supports_vision=True,  # Some models like llava support vision
                supports_system_messages=True,
                supports_temperature=True,
                supports_max_tokens=True,
                token_parameter_name="max_tokens",
                requires_exact_model_name=False,  # Ollama is flexible with names
                supports_model_auto_discovery=True,
                requires_api_key=False,  # Ollama doesn't require auth by default
                supports_custom_endpoint=True,
                default_rate_limit=1000,  # Local, so higher limit
                tracks_token_usage=True,
                supports_cost_estimation=False,  # Local inference, no cost
                custom_features={
                    "local_inference": True,
                    "auto_pull_models": True,
                    "offline_capable": True,
                }
            )
        
        super().__init__(config)
        self.ollama_cli_available = False
    
    def initialize(self) -> None:
        """Initialize Ollama client and check CLI availability."""
        if not self.config.base_url:
            raise ValueError("Ollama base URL is required (e.g., http://localhost:11434)")
        
        try:
            # Check if Ollama CLI is available for model management
            try:
                result = subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                self.ollama_cli_available = (result.returncode == 0)
                if self.ollama_cli_available:
                    logger.info(f"Ollama CLI available: {result.stdout.strip()}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("Ollama CLI not found or not responding")
                self.ollama_cli_available = False
            
            # Create OpenAI-compatible client for Ollama
            self.client = OpenAI(
                base_url=f"{self.config.base_url}/v1",
                api_key=self.config.api_key or "ollama"  # Ollama doesn't need a real key
            )
            
            # Test connection by trying to list models
            try:
                self.client.models.list()
                self._is_initialized = True
                logger.info(f"Ollama provider initialized at {self.config.base_url}")
            except Exception as e:
                logger.warning(f"Could not list Ollama models: {e}")
                # Still mark as initialized if server is reachable
                self._is_initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise ValueError(
                f"Ollama initialization failed: {e}. "
                f"Make sure Ollama is running at {self.config.base_url}"
            )
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using Ollama."""
        if not self._is_initialized:
            raise ValueError("Provider not initialized. Call initialize() first.")
        
        # Use defaults from config
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.default_temperature
        max_tokens = max_tokens or self.config.default_max_tokens
        
        try:
            # Build API parameters
            api_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add any extra parameters
            api_params.update(self.config.extra_params)
            api_params.update(kwargs)
            
            # Call Ollama API (OpenAI-compatible)
            response = self.client.chat.completions.create(**api_params)
            
            # Extract response data
            assistant_message = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0
            
            # Log warning if empty
            if not assistant_message:
                logger.warning(
                    f"Empty response from Ollama. "
                    f"Finish reason: {finish_reason}, Tokens: {tokens_used}"
                )
            
            # Build metadata
            metadata = {
                "tokens_used": tokens_used,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "finish_reason": finish_reason,
                "model_used": model,
                "provider": "ollama",
                "local_inference": True
            }
            
            logger.info(
                f"Ollama response generated: {model}, "
                f"{tokens_used} tokens, finish: {finish_reason}"
            )
            
            return assistant_message, metadata
        
        except APIConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.client.base_url}: {e}")
            raise ValueError(
                f"Cannot connect to Ollama server at {self.config.base_url}. "
                "Please ensure Ollama is installed and running. "
                "Install: https://ollama.ai | Start: 'ollama serve'"
            )
        
        except APIStatusError as e:
            # Handle model not found error with auto-pull
            if e.status_code == 404:
                logger.info(f"Model '{model}' not found, attempting to pull...")
                
                if self.auto_pull_model(model):
                    # Retry after successful pull
                    logger.info(f"Retrying request with pulled model '{model}'...")
                    time.sleep(2)
                    try:
                        response = self.client.chat.completions.create(**api_params)
                        assistant_message = response.choices[0].message.content or ""
                        finish_reason = response.choices[0].finish_reason
                        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                        input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0
                        output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0
                        
                        metadata = {
                            "tokens_used": tokens_used,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "finish_reason": finish_reason,
                            "model_used": model,
                            "provider": "ollama",
                            "local_inference": True,
                            "auto_pulled": True
                        }
                        
                        logger.info(f"Ollama response generated after auto-pull: {model}")
                        return assistant_message, metadata
                    
                    except Exception as retry_error:
                        logger.error(f"Failed after pulling model: {retry_error}")
                        raise ValueError(f"Model pulled but failed to generate: {retry_error}")
                else:
                    raise ValueError(
                        f"Model '{model}' not found and automatic download failed. "
                        f"Try pulling it manually: ollama pull {model}"
                    )
            else:
                logger.error(f"Ollama API error ({e.status_code}): {e}")
                raise ValueError(f"Ollama API error: {e.message if hasattr(e, 'message') else str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}")
            raise ValueError(f"Ollama error: {str(e)}")
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Ollama models."""
        if not self._is_initialized:
            return []
        
        models = []
        
        # Try using CLI first (more detailed info)
        if self.ollama_cli_available:
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    # Skip header line
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if parts:
                                model_name = parts[0]
                                models.append({
                                    "id": model_name,
                                    "name": model_name,
                                    "context_window": 2048,  # Default, varies by model
                                    "description": f"Ollama local model: {model_name}",
                                    "capabilities": self._get_model_capabilities(model_name),
                                    "local": True
                                })
            except Exception as e:
                logger.warning(f"Could not list Ollama models via CLI: {e}")
        
        # Fall back to API if CLI didn't work
        if not models:
            try:
                response = self.client.models.list()
                for model in response.data:
                    models.append({
                        "id": model.id,
                        "name": model.id,
                        "context_window": 2048,
                        "description": f"Ollama model: {model.id}",
                        "capabilities": self._get_model_capabilities(model.id),
                        "local": True
                    })
            except Exception as e:
                logger.warning(f"Could not list Ollama models via API: {e}")
        
        return models
    
    def _get_model_capabilities(self, model_name: str) -> List[str]:
        """Get capabilities for a specific Ollama model."""
        caps = ["chat", "text", "local"]
        
        # Check for vision models
        if any(vision_name in model_name.lower() for vision_name in ['llava', 'bakllava', 'moondream']):
            caps.append("vision")
        
        # Check for coding models
        if any(code_name in model_name.lower() for code_name in ['codellama', 'deepseek-coder', 'starcoder']):
            caps.extend(["coding", "technical"])
        
        # Check for reasoning models
        if any(reason_name in model_name.lower() for reason_name in ['mixtral', 'qwen', 'llama3', 'gemma2']):
            caps.append("reasoning")
        
        return caps
    
    def validate_model(self, model: str) -> bool:
        """Check if a model is valid/available in Ollama."""
        if not self._is_initialized:
            return False
        
        # Check if model is in available models list
        available = self.list_available_models()
        return any(m["id"] == model for m in available)
    
    def check_model_exists(self, model: str) -> bool:
        """Check if a model is already pulled/downloaded."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return model in result.stdout
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Could not check Ollama models")
            return False
    
    def auto_pull_model(self, model: str) -> bool:
        """
        Automatically pull/download an Ollama model.
        
        Args:
            model: Model name to pull
        
        Returns:
            True if successful, False otherwise
        """
        if not self.ollama_cli_available:
            logger.error("Ollama CLI not available for model pulling")
            return False
        
        try:
            logger.info(f"Pulling Ollama model '{model}'... This may take several minutes.")
            
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for large models
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled model '{model}'")
                return True
            else:
                logger.error(f"Failed to pull model '{model}': {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while pulling model '{model}' (exceeded 10 minutes)")
            return False
        except Exception as e:
            logger.error(f"Error pulling model '{model}': {e}")
            return False
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.
        
        Args:
            model: Model name
        
        Returns:
            Dict with model information or None if not found
        """
        if not self.ollama_cli_available:
            return None
        
        try:
            result = subprocess.run(
                ["ollama", "show", model],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse the output for model info
                info = {
                    "name": model,
                    "raw_info": result.stdout,
                    "provider": "ollama"
                }
                return info
        except Exception as e:
            logger.warning(f"Could not get info for model '{model}': {e}")
        
        return None


def create_ollama_provider(
    base_url: str = "http://localhost:11434",
    default_model: str = "llama3.2",
    **kwargs
) -> OllamaProvider:
    """
    Factory function to create an Ollama provider with common defaults.
    
    Args:
        base_url: Ollama server URL
        default_model: Default model to use
        **kwargs: Additional configuration parameters
    
    Returns:
        Configured and initialized OllamaProvider
    """
    config = ProviderConfig(
        provider_name="ollama",
        display_name="Ollama",
        base_url=base_url,
        default_model=default_model,
        **kwargs
    )
    
    provider = OllamaProvider(config)
    provider.initialize()
    return provider

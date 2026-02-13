"""
OpenAI LLM Provider Integration.

This module provides integration with OpenAI's API, including GPT-4, GPT-3.5, and o-series models.
"""
from typing import List, Dict, Optional, Tuple, Any
import openai
from openai import OpenAI, APIConnectionError, APIStatusError

from .base_provider import BaseLLMProvider, ProviderConfig, ProviderCapabilities
from logger import logger


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation supporting GPT models."""
    
    # Known OpenAI models with their properties
    MODEL_INFO = {
        "gpt-4o": {
            "name": "GPT-4 Optimized",
            "context_window": 128000,
            "supports_temperature": True,
            "description": "Most capable GPT-4 model, optimized for speed and cost"
        },
        "gpt-4o-mini": {
            "name": "GPT-4 Optimized Mini",
            "context_window": 128000,
            "supports_temperature": True,
            "description": "Smaller, faster GPT-4 model"
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "context_window": 128000,
            "supports_temperature": True,
            "description": "Enhanced GPT-4 with vision capabilities"
        },
        "gpt-4": {
            "name": "GPT-4",
            "context_window": 8192,
            "supports_temperature": True,
            "description": "Standard GPT-4 model"
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "context_window": 16385,
            "supports_temperature": True,
            "description": "Fast and efficient model"
        },
        "o1": {
            "name": "O1 (Reasoning)",
            "context_window": 200000,
            "supports_temperature": False,
            "description": "Advanced reasoning model with fixed temperature"
        },
        "o1-mini": {
            "name": "O1 Mini",
            "context_window": 128000,
            "supports_temperature": False,
            "description": "Smaller reasoning model"
        },
        "o3": {
            "name": "O3 (Advanced Reasoning)",
            "context_window": 200000,
            "supports_temperature": False,
            "description": "Next-generation reasoning model"
        },
        "o3-mini": {
            "name": "O3 Mini",
            "context_window": 128000,
            "supports_temperature": False,
            "description": "Efficient reasoning model"
        }
    }
    
    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider with configuration."""
        # Set OpenAI-specific capabilities
        if not config.capabilities:
            config.capabilities = ProviderCapabilities(
                supports_streaming=True,
                supports_function_calling=True,
                supports_vision=True,
                supports_system_messages=True,
                supports_temperature=True,
                supports_max_tokens=True,
                token_parameter_name="max_tokens",
                requires_exact_model_name=True,
                supports_model_auto_discovery=True,
                requires_api_key=True,
                supports_custom_endpoint=True,
                default_rate_limit=60,
                tracks_token_usage=True,
                supports_cost_estimation=True
            )
        
        super().__init__(config)
    
    def initialize(self) -> None:
        """Initialize OpenAI client and validate API key."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")
        
        try:
            # Set global API key for backward compatibility
            openai.api_key = self.config.api_key
            
            # Create client
            if self.config.base_url:
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
            else:
                self.client = OpenAI(api_key=self.config.api_key)
            
            # Test the connection by listing models
            try:
                self.client.models.list()
                self._is_initialized = True
                logger.info(f"OpenAI provider initialized successfully")
            except Exception as e:
                logger.warning(f"OpenAI API key validation skipped (may fail on some plans): {e}")
                # Some API keys don't have model list access, but can still generate
                self._is_initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise ValueError(f"OpenAI initialization failed: {e}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using OpenAI API."""
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
                "max_tokens": max_tokens,
            }
            
            # Check if model supports temperature
            model_info = self.MODEL_INFO.get(model, {})
            supports_temp = model_info.get("supports_temperature", True)
            
            # O-series models (o1, o3) don't support custom temperature
            if not model.startswith(('o1', 'o3')) and supports_temp:
                api_params["temperature"] = temperature
            
            # Add any extra parameters from config or kwargs
            api_params.update(self.config.extra_params)
            api_params.update(kwargs)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            # Extract response data
            assistant_message = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens if response.usage else 0
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            # Log warning if empty
            if not assistant_message:
                logger.warning(
                    f"Empty response from OpenAI. "
                    f"Finish reason: {finish_reason}, Tokens: {tokens_used}"
                )
            
            # Build metadata
            metadata = {
                "tokens_used": tokens_used,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "finish_reason": finish_reason,
                "model_used": model,
                "provider": "openai"
            }
            
            # Add cost estimate if available
            cost = self.estimate_cost(input_tokens, output_tokens, model)
            if cost is not None:
                metadata["estimated_cost_usd"] = cost
            
            logger.info(
                f"OpenAI response generated: {model}, "
                f"{tokens_used} tokens, finish: {finish_reason}"
            )
            
            return assistant_message, metadata
        
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise ValueError(f"Cannot connect to OpenAI API: {e}")
        
        except APIStatusError as e:
            logger.error(f"OpenAI API error ({e.status_code}): {e}")
            raise ValueError(f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e}")
            raise ValueError(f"OpenAI error: {str(e)}")
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available OpenAI models."""
        if not self._is_initialized:
            # Return known models even if not initialized
            return [
                {
                    "id": model_id,
                    "name": info["name"],
                    "context_window": info["context_window"],
                    "description": info["description"],
                    "capabilities": self._get_model_capabilities(model_id, info)
                }
                for model_id, info in self.MODEL_INFO.items()
            ]
        
        try:
            # Try to fetch live model list
            models_response = self.client.models.list()
            live_models = []
            
            for model in models_response.data:
                model_id = model.id
                # Only include chat models
                if any(prefix in model_id for prefix in ['gpt', 'o1', 'o3']):
                    info = self.MODEL_INFO.get(model_id, {
                        "name": model_id,
                        "context_window": 4096,
                        "description": f"OpenAI model: {model_id}"
                    })
                    
                    live_models.append({
                        "id": model_id,
                        "name": info.get("name", model_id),
                        "context_window": info.get("context_window", 4096),
                        "description": info.get("description", ""),
                        "capabilities": self._get_model_capabilities(model_id, info)
                    })
            
            return live_models if live_models else self.list_available_models.__wrapped__(self)
        
        except Exception as e:
            logger.warning(f"Could not fetch live OpenAI models: {e}")
            # Fall back to known models
            return [
                {
                    "id": model_id,
                    "name": info["name"],
                    "context_window": info["context_window"],
                    "description": info["description"],
                    "capabilities": self._get_model_capabilities(model_id, info)
                }
                for model_id, info in self.MODEL_INFO.items()
            ]
    
    def _get_model_capabilities(self, model_id: str, info: Dict) -> List[str]:
        """Get capabilities for a specific model."""
        caps = ["chat", "text"]
        
        if "gpt-4" in model_id:
            caps.append("advanced-reasoning")
            if "turbo" in model_id or "o" in model_id:
                caps.append("vision")
        
        if model_id.startswith(('o1', 'o3')):
            caps.extend(["reasoning", "complex-tasks"])
        
        return caps
    
    def validate_model(self, model: str) -> bool:
        """Check if a model is valid for OpenAI."""
        # Check against known models
        if model in self.MODEL_INFO:
            return True
        
        # Check if model follows OpenAI naming patterns
        valid_prefixes = ['gpt-', 'o1', 'o3', 'text-', 'davinci', 'curie', 'babbage', 'ada']
        return any(model.startswith(prefix) for prefix in valid_prefixes)
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> Optional[float]:
        """
        Estimate cost for OpenAI API call.
        
        Prices as of 2026 (approximate, check OpenAI pricing for current rates).
        """
        model = model or self.config.default_model
        
        # Pricing per 1M tokens (input, output)
        PRICING = {
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4-turbo": (10.00, 30.00),
            "gpt-4": (30.00, 60.00),
            "gpt-3.5-turbo": (0.50, 1.50),
            "o1": (15.00, 60.00),
            "o1-mini": (3.00, 12.00),
            "o3": (20.00, 80.00),
            "o3-mini": (5.00, 20.00),
        }
        
        if model in PRICING:
            input_price, output_price = PRICING[model]
            cost = (input_tokens / 1_000_000 * input_price) + \
                   (output_tokens / 1_000_000 * output_price)
            return round(cost, 6)
        
        return None


def create_openai_provider(
    api_key: str,
    default_model: str = "gpt-4o",
    base_url: Optional[str] = None,
    **kwargs
) -> OpenAIProvider:
    """
    Factory function to create an OpenAI provider with common defaults.
    
    Args:
        api_key: OpenAI API key
        default_model: Default model to use
        base_url: Optional custom API endpoint
        **kwargs: Additional configuration parameters
    
    Returns:
        Configured and initialized OpenAIProvider
    """
    config = ProviderConfig(
        provider_name="openai",
        display_name="OpenAI",
        api_key=api_key,
        base_url=base_url,
        default_model=default_model,
        **kwargs
    )
    
    provider = OpenAIProvider(config)
    provider.initialize()
    return provider

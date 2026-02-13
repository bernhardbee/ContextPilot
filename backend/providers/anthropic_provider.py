"""
Anthropic LLM Provider Integration.

This module provides integration with Anthropic's Claude API.
"""
from typing import List, Dict, Optional, Tuple, Any
from anthropic import Anthropic, APIConnectionError, APIStatusError

from .base_provider import BaseLLMProvider, ProviderConfig, ProviderCapabilities
from logger import logger


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation for Claude models."""
    
    # Known Claude models with their properties
    MODEL_INFO = {
        "claude-3-7-sonnet-20250219": {
            "name": "Claude 3.7 Sonnet",
            "context_window": 200000,
            "description": "Most balanced Claude model with extended context"
        },
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "context_window": 200000,
            "description": "Advanced reasoning and coding capabilities"
        },
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "context_window": 200000,
            "description": "Fast, efficient model for everyday tasks"
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "context_window": 200000,
            "description": "Most capable Claude model for complex tasks"
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "context_window": 200000,
            "description": "Balanced performance and speed"
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "context_window": 200000,
            "description": "Fast responses for simple tasks"
        }
    }
    
    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider with configuration."""
        # Set Anthropic-specific capabilities
        if not config.capabilities:
            config.capabilities = ProviderCapabilities(
                supports_streaming=True,
                supports_function_calling=True,  # Claude supports tools
                supports_vision=True,  # Claude 3+ supports vision
                supports_system_messages=False,  # Uses different system message format
                supports_temperature=True,
                supports_max_tokens=True,
                token_parameter_name="max_tokens",
                requires_exact_model_name=True,
                supports_model_auto_discovery=False,
                requires_api_key=True,
                supports_custom_endpoint=False,
                default_rate_limit=50,
                tracks_token_usage=True,
                supports_cost_estimation=True,
                custom_features={
                    "system_parameter": True,  # System message as separate parameter
                    "thinking_tokens": True,  # Extended thinking mode
                }
            )
        
        super().__init__(config)
    
    def initialize(self) -> None:
        """Initialize Anthropic client and validate API key."""
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")
        
        try:
            # Create Anthropic client
            self.client = Anthropic(api_key=self.config.api_key)
            
            # Anthropic doesn't have a simple health check endpoint
            # Mark as initialized if client created successfully
            self._is_initialized = True
            logger.info("Anthropic provider initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise ValueError(f"Anthropic initialization failed: {e}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using Anthropic API."""
        if not self._is_initialized:
            raise ValueError("Provider not initialized. Call initialize() first.")
        
        # Use defaults from config
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.default_temperature
        max_tokens = max_tokens or self.config.default_max_tokens
        
        try:
            # Anthropic uses system parameter separately from messages
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            # Build API parameters
            api_params = {
                "model": model,
                "messages": user_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Add system message if present
            if system_message:
                api_params["system"] = system_message
            
            # Add any extra parameters from config or kwargs
            api_params.update(self.config.extra_params)
            api_params.update(kwargs)
            
            # Call Anthropic API
            response = self.client.messages.create(**api_params)
            
            # Extract response data
            assistant_message = response.content[0].text
            finish_reason = response.stop_reason
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            tokens_used = input_tokens + output_tokens
            
            # Log warning if empty
            if not assistant_message:
                logger.warning(
                    f"Empty response from Anthropic. "
                    f"Stop reason: {finish_reason}, Tokens: {tokens_used}"
                )
            
            # Build metadata
            metadata = {
                "tokens_used": tokens_used,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "finish_reason": finish_reason,
                "model_used": model,
                "provider": "anthropic"
            }
            
            # Add cost estimate if available
            cost = self.estimate_cost(input_tokens, output_tokens, model)
            if cost is not None:
                metadata["estimated_cost_usd"] = cost
            
            logger.info(
                f"Anthropic response generated: {model}, "
                f"{tokens_used} tokens, stop: {finish_reason}"
            )
            
            return assistant_message, metadata
        
        except APIConnectionError as e:
            logger.error(f"Anthropic connection error: {e}")
            raise ValueError(f"Cannot connect to Anthropic API: {e}")
        
        except APIStatusError as e:
            logger.error(f"Anthropic API error ({e.status_code}): {e}")
            raise ValueError(f"Anthropic API error: {e.message if hasattr(e, 'message') else str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected Anthropic error: {e}")
            raise ValueError(f"Anthropic error: {str(e)}")
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Anthropic models."""
        return [
            {
                "id": model_id,
                "name": info["name"],
                "context_window": info["context_window"],
                "description": info["description"],
                "capabilities": self._get_model_capabilities(model_id)
            }
            for model_id, info in self.MODEL_INFO.items()
        ]
    
    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """Get capabilities for a specific model."""
        caps = ["chat", "text", "vision"]
        
        if "opus" in model_id:
            caps.extend(["advanced-reasoning", "complex-tasks", "long-context"])
        elif "sonnet" in model_id:
            caps.extend(["reasoning", "coding", "analysis"])
        elif "haiku" in model_id:
            caps.extend(["fast", "efficient"])
        
        return caps
    
    def validate_model(self, model: str) -> bool:
        """Check if a model is valid for Anthropic."""
        # Check against known models
        if model in self.MODEL_INFO:
            return True
        
        # Check if model follows Claude naming pattern
        return model.startswith("claude-")
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> Optional[float]:
        """
        Estimate cost for Anthropic API call.
        
        Prices as of 2026 (approximate, check Anthropic pricing for current rates).
        """
        model = model or self.config.default_model
        
        # Pricing per 1M tokens (input, output)
        PRICING = {
            "claude-3-7-sonnet-20250219": (3.00, 15.00),
            "claude-3-5-sonnet-20241022": (3.00, 15.00),
            "claude-3-5-haiku-20241022": (0.80, 4.00),
            "claude-3-opus-20240229": (15.00, 75.00),
            "claude-3-sonnet-20240229": (3.00, 15.00),
            "claude-3-haiku-20240307": (0.25, 1.25),
        }
        
        if model in PRICING:
            input_price, output_price = PRICING[model]
            cost = (input_tokens / 1_000_000 * input_price) + \
                   (output_tokens / 1_000_000 * output_price)
            return round(cost, 6)
        
        return None
    
    def prepare_messages(
        self,
        prompt,
        conversation_messages: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Prepare messages for Anthropic format.
        
        Anthropic doesn't include system messages in the messages array;
        they're passed separately. This override handles that.
        """
        messages = []
        
        # Add conversation history (excluding system messages)
        if conversation_messages:
            messages.extend([
                msg for msg in conversation_messages
                if msg.get("role") != "system"
            ])
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt.generated_prompt
        })
        
        return messages


def create_anthropic_provider(
    api_key: str,
    default_model: str = "claude-3-7-sonnet-20250219",
    **kwargs
) -> AnthropicProvider:
    """
    Factory function to create an Anthropic provider with common defaults.
    
    Args:
        api_key: Anthropic API key
        default_model: Default model to use
        **kwargs: Additional configuration parameters
    
    Returns:
        Configured and initialized AnthropicProvider
    """
    config = ProviderConfig(
        provider_name="anthropic",
        display_name="Anthropic",
        api_key=api_key,
        default_model=default_model,
        **kwargs
    )
    
    provider = AnthropicProvider(config)
    provider.initialize()
    return provider

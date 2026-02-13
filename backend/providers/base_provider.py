"""
Base abstract class for LLM provider integrations.

This module defines the interface that all LLM providers must implement,
ensuring consistent behavior across different vendors.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from models import GeneratedPrompt
from db_models import ConversationDB


@dataclass
class ProviderCapabilities:
    """Defines the capabilities of an LLM provider."""
    
    # Feature support
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_system_messages: bool = True
    supports_temperature: bool = True
    supports_max_tokens: bool = True
    
    # Token handling
    token_parameter_name: str = "max_tokens"  # Some models use max_completion_tokens
    requires_exact_model_name: bool = True
    supports_model_auto_discovery: bool = False
    
    # Authentication
    requires_api_key: bool = True
    supports_custom_endpoint: bool = False
    
    # Rate limits (requests per minute)
    default_rate_limit: int = 60
    
    # Cost management
    tracks_token_usage: bool = True
    supports_cost_estimation: bool = False
    
    # Additional features
    custom_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    
    # Basic configuration
    provider_name: str
    display_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Model defaults
    default_model: str = ""
    available_models: List[str] = field(default_factory=list)
    
    # Request defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    timeout_seconds: int = 300
    
    # Advanced settings
    custom_headers: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    # Capabilities
    capabilities: Optional[ProviderCapabilities] = None
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the provider configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.capabilities and self.capabilities.requires_api_key and not self.api_key:
            return False, f"{self.display_name} requires an API key"
        
        if not self.default_model and self.available_models:
            return False, f"{self.display_name} must have a default model"
        
        if self.default_temperature < 0 or self.default_temperature > 2:
            return False, "Temperature must be between 0 and 2"
        
        if self.default_max_tokens <= 0:
            return False, "Max tokens must be positive"
        
        return True, None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider integrations.
    
    Each provider (OpenAI, Anthropic, Ollama, etc.) must implement this interface
    to ensure consistent behavior and easy extensibility.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.client = None
        self._is_initialized = False
        
        # Validate configuration
        is_valid, error = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid provider configuration: {error}")
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the provider (create API client, validate connection, etc.).
        
        This method should:
        1. Create the API client
        2. Validate credentials
        3. Set up any necessary connections
        4. Mark provider as initialized
        
        Raises:
            ValueError: If initialization fails
        """
        pass
    
    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to provider's default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific additional parameters
        
        Returns:
            Tuple of (response_text, metadata_dict)
            metadata should include: tokens_used, finish_reason, model_used, etc.
        
        Raises:
            ValueError: If generation fails or invalid parameters
        """
        pass
    
    @abstractmethod
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of dicts with model information:
            [
                {
                    "id": "model-id",
                    "name": "Display Name",
                    "context_window": 4096,
                    "description": "Model description",
                    "capabilities": ["chat", "vision", etc.]
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """
        Check if a model is valid/available for this provider.
        
        Args:
            model: Model identifier to validate
        
        Returns:
            True if model is valid, False otherwise
        """
        pass
    
    def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of this provider.
        
        Returns:
            ProviderCapabilities object
        """
        return self.config.capabilities
    
    def is_initialized(self) -> bool:
        """Check if the provider is initialized and ready to use."""
        return self._is_initialized
    
    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the provider is healthy and can process requests.
        
        Returns:
            Tuple of (is_healthy, error_message)
        """
        if not self.is_initialized():
            return False, "Provider not initialized"
        
        try:
            # Try to list models as a health check
            self.list_available_models()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> Optional[float]:
        """
        Estimate the cost for a request (if provider supports it).
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model being used
        
        Returns:
            Estimated cost in USD, or None if not supported
        """
        return None  # Override in subclass if supported
    
    def prepare_messages(
        self,
        prompt: GeneratedPrompt,
        conversation_messages: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Prepare messages in the format expected by this provider.
        
        This method can be overridden by providers that need special message formatting.
        
        Args:
            prompt: The generated prompt for the current request
            conversation_messages: Previous messages in the conversation
        
        Returns:
            List of formatted messages
        """
        messages = []
        
        # Add system message if supported
        if self.config.capabilities.supports_system_messages:
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant with access to personalized context."
            })
        
        # Add conversation history
        if conversation_messages:
            messages.extend(conversation_messages)
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt.generated_prompt
        })
        
        return messages
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.config.provider_name}', "
            f"initialized={self._is_initialized})"
        )

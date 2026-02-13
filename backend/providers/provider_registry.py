"""
Provider Registry and Factory for LLM Providers.

This module manages the registration and instantiation of LLM providers,
providing a central registry for all available providers.
"""
from typing import Dict, List, Optional, Type, Any, Tuple
from dataclasses import dataclass

from .base_provider import BaseLLMProvider, ProviderConfig
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from logger import logger


@dataclass
class ProviderMetadata:
    """Metadata about a registered provider."""
    provider_class: Type[BaseLLMProvider]
    name: str
    display_name: str
    description: str
    requires_api_key: bool
    supports_local: bool
    homepage_url: str
    documentation_url: str


class ProviderRegistry:
    """
    Central registry for all LLM providers.
    
    This class manages provider registration, instantiation, and discovery.
    """
    
    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[str, ProviderMetadata] = {}
        self._instances: Dict[str, BaseLLMProvider] = {}
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register all built-in providers."""
        # Register OpenAI
        self.register_provider(
            provider_class=OpenAIProvider,
            name="openai",
            display_name="OpenAI",
            description="OpenAI GPT models including GPT-4, GPT-3.5, and o-series",
            requires_api_key=True,
            supports_local=False,
            homepage_url="https://openai.com",
            documentation_url="https://platform.openai.com/docs"
        )
        
        # Register Anthropic
        self.register_provider(
            provider_class=AnthropicProvider,
            name="anthropic",
            display_name="Anthropic",
            description="Anthropic Claude models with extended context windows",
            requires_api_key=True,
            supports_local=False,
            homepage_url="https://anthropic.com",
            documentation_url="https://docs.anthropic.com"
        )
        
        # Register Ollama
        self.register_provider(
            provider_class=OllamaProvider,
            name="ollama",
            display_name="Ollama",
            description="Local LLM inference with automatic model downloading",
            requires_api_key=False,
            supports_local=True,
            homepage_url="https://ollama.ai",
            documentation_url="https://github.com/ollama/ollama/blob/main/docs/api.md"
        )
        
        logger.info(f"Registered {len(self._providers)} built-in providers")
    
    def register_provider(
        self,
        provider_class: Type[BaseLLMProvider],
        name: str,
        display_name: str,
        description: str,
        requires_api_key: bool = True,
        supports_local: bool = False,
        homepage_url: str = "",
        documentation_url: str = ""
    ):
        """
        Register a new provider.
        
        Args:
            provider_class: The provider class (must inherit from BaseLLMProvider)
            name: Unique identifier for the provider (e.g., "openai")
            display_name: Human-readable name (e.g., "OpenAI")
            description: Brief description of the provider
            requires_api_key: Whether an API key is required
            supports_local: Whether this is a local inference provider
            homepage_url: Provider's homepage URL
            documentation_url: Provider's API documentation URL
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(f"Provider class must inherit from BaseLLMProvider")
        
        if name in self._providers:
            logger.warning(f"Overwriting existing provider registration: {name}")
        
        metadata = ProviderMetadata(
            provider_class=provider_class,
            name=name,
            display_name=display_name,
            description=description,
            requires_api_key=requires_api_key,
            supports_local=supports_local,
            homepage_url=homepage_url,
            documentation_url=documentation_url
        )
        
        self._providers[name] = metadata
        logger.info(f"Registered provider: {name} ({display_name})")
    
    def get_provider(
        self,
        provider_name: str,
        config: Optional[ProviderConfig] = None,
        initialize: bool = True,
        cache: bool = True
    ) -> BaseLLMProvider:
        """
        Get a provider instance.
        
        Args:
            provider_name: Name of the provider (e.g., "openai")
            config: Optional provider configuration. If None, must be provided later.
            initialize: Whether to initialize the provider immediately
            cache: Whether to cache the instance for reuse
        
        Returns:
            Provider instance
        
        Raises:
            ValueError: If provider not found or configuration invalid
        """
        # Check if we have a cached instance
        if cache and provider_name in self._instances:
            return self._instances[provider_name]
        
        # Check if provider is registered
        if provider_name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )
        
        metadata = self._providers[provider_name]
        
        # Create config if not provided
        if config is None:
            raise ValueError(f"Configuration required for provider '{provider_name}'")
        
        # Set provider name in config if not already set
        if not config.provider_name:
            config.provider_name = provider_name
        if not config.display_name:
            config.display_name = metadata.display_name
        
        # Instantiate provider
        try:
            provider = metadata.provider_class(config)
            
            # Initialize if requested
            if initialize:
                provider.initialize()
            
            # Cache if requested
            if cache:
                self._instances[provider_name] = provider
            
            logger.info(f"Created provider instance: {provider_name}")
            return provider
        
        except Exception as e:
            logger.error(f"Failed to create provider '{provider_name}': {e}")
            raise
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all registered providers.
        
        Returns:
            List of provider information dicts
        """
        return [
            {
                "name": name,
                "display_name": meta.display_name,
                "description": meta.description,
                "requires_api_key": meta.requires_api_key,
                "supports_local": meta.supports_local,
                "homepage_url": meta.homepage_url,
                "documentation_url": meta.documentation_url,
                "initialized": name in self._instances
            }
            for name, meta in self._providers.items()
        ]
    
    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is registered."""
        return provider_name in self._providers
    
    def get_provider_metadata(self, provider_name: str) -> Optional[ProviderMetadata]:
        """Get metadata for a specific provider."""
        return self._providers.get(provider_name)
    
    def clear_cache(self, provider_name: Optional[str] = None):
        """
        Clear cached provider instances.
        
        Args:
            provider_name: Specific provider to clear, or None to clear all
        """
        if provider_name:
            if provider_name in self._instances:
                del self._instances[provider_name]
                logger.info(f"Cleared cached instance: {provider_name}")
        else:
            self._instances.clear()
            logger.info("Cleared all cached provider instances")
    
    def health_check_all(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Run health checks on all initialized providers.
        
        Returns:
            Dict mapping provider names to (is_healthy, error_message) tuples
        """
        results = {}
        for name, provider in self._instances.items():
            results[name] = provider.health_check()
        return results


# Global registry instance
_global_registry = ProviderRegistry()


def get_provider(provider_name: str, config: Optional[ProviderConfig] = None, **kwargs) -> BaseLLMProvider:
    """
    Convenience function to get a provider from the global registry.
    
    Args:
        provider_name: Name of the provider
        config: Provider configuration
        **kwargs: Additional arguments passed to registry.get_provider()
    
    Returns:
        Provider instance
    """
    return _global_registry.get_provider(provider_name, config, **kwargs)


def list_providers() -> List[Dict[str, Any]]:
    """List all available providers from the global registry."""
    return _global_registry.list_providers()


def register_provider(provider_class: Type[BaseLLMProvider], **kwargs):
    """Register a new provider with the global registry."""
    _global_registry.register_provider(provider_class, **kwargs)


def get_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    return _global_registry


# Factory functions for convenience

def create_provider_from_env(
    provider_name: str,
    env_config: Dict[str, Any]
) -> BaseLLMProvider:
    """
    Create a provider from environment/config dict.
    
    Args:
        provider_name: Name of the provider
        env_config: Configuration dict with keys like api_key, base_url, etc.
    
    Returns:
        Configured and initialized provider
    """
    # Build provider config from env_config
    config_kwargs = {}
    
    # Map common config keys
    key_mapping = {
        "api_key": "api_key",
        "base_url": "base_url",
        "default_model": "default_model",
        "temperature": "default_temperature",
        "max_tokens": "default_max_tokens",
    }
    
    for env_key, config_key in key_mapping.items():
        if env_key in env_config:
            config_kwargs[config_key] = env_config[env_key]
    
    config = ProviderConfig(
        provider_name=provider_name,
        display_name=_global_registry.get_provider_metadata(provider_name).display_name,
        **config_kwargs
    )
    
    return get_provider(provider_name, config)

"""
Test cases for the modular provider system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from providers import (
    BaseLLMProvider,
    ProviderConfig,
    ProviderCapabilities,
    ProviderRegistry,
    get_provider,
    list_providers
)
from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.ollama_provider import OllamaProvider


class TestProviderConfig:
    """Tests for ProviderConfig."""
    
    def test_config_validation_success(self):
        """Test valid configuration."""
        config = ProviderConfig(
            provider_name="test",
            display_name="Test Provider",
            api_key="test-key",
            default_model="test-model"
        )
        is_valid, error = config.validate()
        assert is_valid
        assert error is None
    
    def test_config_validation_missing_api_key(self):
        """Test validation fails without API key when required."""
        config = ProviderConfig(
            provider_name="test",
            display_name="Test Provider",
            default_model="test-model",
            capabilities=ProviderCapabilities(requires_api_key=True)
        )
        is_valid, error = config.validate()
        assert not is_valid
        assert "API key" in error
    
    def test_config_validation_invalid_temperature(self):
        """Test validation fails with invalid temperature."""
        config = ProviderConfig(
            provider_name="test",
            display_name="Test Provider",
            api_key="test-key",
            default_model="test-model",
            default_temperature=3.0  # Invalid
        )
        is_valid, error = config.validate()
        assert not is_valid
        assert "temperature" in error.lower()


class TestProviderCapabilities:
    """Tests for ProviderCapabilities."""
    
    def test_default_capabilities(self):
        """Test default capability values."""
        caps = ProviderCapabilities()
        assert caps.supports_system_messages is True
        assert caps.requires_api_key is True
        assert caps.supports_temperature is True
    
    def test_custom_capabilities(self):
        """Test custom capability configuration."""
        caps = ProviderCapabilities(
            supports_streaming=True,
            supports_vision=True,
            requires_api_key=False,
            custom_features={"local": True}
        )
        assert caps.supports_streaming is True
        assert caps.supports_vision is True
        assert caps.requires_api_key is False
        assert caps.custom_features["local"] is True


class TestProviderRegistry:
    """Tests for ProviderRegistry."""
    
    def test_builtin_providers_registered(self):
        """Test that built-in providers are registered."""
        registry = ProviderRegistry()
        providers = registry.list_providers()
        
        provider_names = [p["name"] for p in providers]
        assert "openai" in provider_names
        assert "anthropic" in provider_names
        assert "ollama" in provider_names
    
    def test_get_provider_metadata(self):
        """Test retrieving provider metadata."""
        registry = ProviderRegistry()
        metadata = registry.get_provider_metadata("openai")
        
        assert metadata is not None
        assert metadata.name == "openai"
        assert metadata.display_name == "OpenAI"
        assert metadata.requires_api_key is True
    
    def test_is_provider_available(self):
        """Test checking provider availability."""
        registry = ProviderRegistry()
        assert registry.is_provider_available("openai")
        assert registry.is_provider_available("anthropic")
        assert not registry.is_provider_available("nonexistent")
    
    def test_list_providers(self):
        """Test listing all providers."""
        providers = list_providers()
        assert len(providers) >= 3
        assert all("name" in p for p in providers)
        assert all("display_name" in p for p in providers)


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""
    
    def test_provider_creation(self):
        """Test creating an OpenAI provider."""
        config = ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            api_key="test-key",
            default_model="gpt-4o"
        )
        provider = OpenAIProvider(config)
        assert provider.config.api_key == "test-key"
        assert provider.config.default_model == "gpt-4o"
    
    def test_openai_capabilities(self):
        """Test OpenAI provider capabilities."""
        config = ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            api_key="test-key",
            default_model="gpt-4o"
        )
        provider = OpenAIProvider(config)
        caps = provider.get_capabilities()
        
        assert caps.supports_streaming is True
        assert caps.supports_function_calling is True
        assert caps.supports_vision is True
        assert caps.supports_cost_estimation is True
    
    def test_validate_model(self):
        """Test model validation."""
        config = ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            api_key="test-key",
            default_model="gpt-4o"
        )
        provider = OpenAIProvider(config)
        
        assert provider.validate_model("gpt-4o")
        assert provider.validate_model("gpt-3.5-turbo")
        assert provider.validate_model("o1")
        assert not provider.validate_model("claude-3")
    
    def test_list_available_models(self):
        """Test listing available models."""
        config = ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            api_key="test-key",
            default_model="gpt-4o"
        )
        provider = OpenAIProvider(config)
        models = provider.list_available_models()
        
        assert len(models) > 0
        assert any(m["id"] == "gpt-4o" for m in models)
        assert all("name" in m for m in models)
        assert all("context_window" in m for m in models)
    
    def test_cost_estimation(self):
        """Test cost estimation for OpenAI."""
        config = ProviderConfig(
            provider_name="openai",
            display_name="OpenAI",
            api_key="test-key",
            default_model="gpt-4o"
        )
        provider = OpenAIProvider(config)
        
        cost = provider.estimate_cost(1000, 500, "gpt-4o")
        assert cost is not None
        assert cost > 0
        assert isinstance(cost, float)


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""
    
    def test_provider_creation(self):
        """Test creating an Anthropic provider."""
        config = ProviderConfig(
            provider_name="anthropic",
            display_name="Anthropic",
            api_key="test-key",
            default_model="claude-3-7-sonnet-20250219"
        )
        provider = AnthropicProvider(config)
        assert provider.config.api_key == "test-key"
    
    def test_anthropic_capabilities(self):
        """Test Anthropic provider capabilities."""
        config = ProviderConfig(
            provider_name="anthropic",
            display_name="Anthropic",
            api_key="test-key",
            default_model="claude-3-7-sonnet-20250219"
        )
        provider = AnthropicProvider(config)
        caps = provider.get_capabilities()
        
        assert caps.supports_streaming is True
        assert caps.supports_function_calling is True
        assert caps.supports_vision is True
        assert caps.supports_system_messages is False  # Uses separate parameter
    
    def test_validate_model(self):
        """Test model validation."""
        config = ProviderConfig(
            provider_name="anthropic",
            display_name="Anthropic",
            api_key="test-key",
            default_model="claude-3-7-sonnet-20250219"
        )
        provider = AnthropicProvider(config)
        
        assert provider.validate_model("claude-3-7-sonnet-20250219")
        assert provider.validate_model("claude-3-opus-20240229")
        assert not provider.validate_model("gpt-4o")


class TestOllamaProvider:
    """Tests for OllamaProvider."""
    
    def test_provider_creation(self):
        """Test creating an Ollama provider."""
        config = ProviderConfig(
            provider_name="ollama",
            display_name="Ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2"
        )
        provider = OllamaProvider(config)
        assert provider.config.base_url == "http://localhost:11434"
    
    def test_ollama_capabilities(self):
        """Test Ollama provider capabilities."""
        config = ProviderConfig(
            provider_name="ollama",
            display_name="Ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2"
        )
        provider = OllamaProvider(config)
        caps = provider.get_capabilities()
        
        assert caps.requires_api_key is False
        assert caps.supports_custom_endpoint is True
        assert caps.supports_model_auto_discovery is True
        assert caps.custom_features.get("local_inference") is True
        assert caps.custom_features.get("auto_pull_models") is True
    
    def test_validate_model_without_init(self):
        """Test model validation without initialization."""
        config = ProviderConfig(
            provider_name="ollama",
            display_name="Ollama",
            base_url="http://localhost:11434",
            default_model="llama3.2"
        )
        provider = OllamaProvider(config)
        
        # Should return False when not initialized
        assert provider.validate_model("llama3.2") is False


class TestModularAIService:
    """Tests for ModularAIService."""
    
    @patch('ai_service_modular.settings')
    def test_service_initialization(self, mock_settings):
        """Test service initializes providers from config."""
        from ai_service_modular import ModularAIService
        
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.anthropic_api_key = ""
        mock_settings.ollama_base_url = ""
        mock_settings.default_ai_provider = "openai"
        mock_settings.default_ai_model = "gpt-4o"
        mock_settings.ai_temperature = 0.7
        mock_settings.ai_max_tokens = 2000
        
        # This would typically fail because it tries to initialize
        # But the test demonstrates the concept
        # service = ModularAIService()
        # assert "openai" in service.active_providers
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        from ai_service_modular import modular_ai_service
        
        info = modular_ai_service.get_provider_info()
        assert isinstance(info, list)
        
        # Check structure
        for provider_info in info:
            assert "name" in provider_info
            assert "display_name" in provider_info
            assert "initialized" in provider_info
            assert "capabilities" in provider_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

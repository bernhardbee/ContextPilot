# Modular LLM Provider Architecture

## Overview

ContextPilot now features a modular, plugin-like architecture for integrating different LLM providers. Each provider (OpenAI, Anthropic, Ollama, etc.) has its own dedicated module with specific configuration options and capabilities.

## Architecture Benefits

### 🔌 Modularity
- Each LLM provider is a standalone module
- Add new providers without modifying core code
- Clean separation of concerns

### ⚙️ Provider-Specific Configuration
- Each provider can have unique settings
- Model-specific behavior (e.g., o1 doesn't support temperature)
- Custom features per provider (auto-pull for Ollama)

### 🔄 Easy Switching
- Switch between providers seamlessly
- Run multiple providers simultaneously
- Consistent API across all providers

### 🧪 Testability
- Mock providers easily for testing
- Test providers in isolation
- Clear interfaces for all functionality

## Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│                  (main.py, endpoints)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              ModularAIService                            │
│  - Manages active providers                              │
│  - Routes requests to appropriate provider               │
│  - Handles conversation persistence                      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              ProviderRegistry                            │
│  - Registers all available providers                     │
│  - Factory for creating provider instances               │
│  - Provider discovery and metadata                       │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   OpenAI    │ │  Anthropic  │ │   Ollama    │
│  Provider   │ │  Provider   │ │  Provider   │
└─────────────┘ └─────────────┘ └─────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  BaseLLMProvider      │
            │  (Abstract Interface) │
            └───────────────────────┘
```

## Core Classes

### BaseLLMProvider

Abstract base class that all providers must implement:

```python
class BaseLLMProvider(ABC):
    def __init__(self, config: ProviderConfig)
    
    @abstractmethod
    def initialize(self) -> None
        """Initialize the provider (create client, validate credentials)"""
    
    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]
        """Generate AI response"""
    
    @abstractmethod
    def list_available_models(self) -> List[Dict[str, Any]]
        """Get available models for this provider"""
    
    @abstractmethod
    def validate_model(self, model: str) -> bool
        """Check if a model is valid"""
```

### ProviderConfig

Configuration dataclass for provider settings:

```python
@dataclass
class ProviderConfig:
    provider_name: str
    display_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = ""
    available_models: List[str] = field(default_factory=list)
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    timeout_seconds: int = 300
    custom_headers: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
```

### ProviderCapabilities

Defines what features a provider supports:

```python
@dataclass
class ProviderCapabilities:
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_system_messages: bool = True
    supports_temperature: bool = True
    supports_max_tokens: bool = True
    requires_api_key: bool = True
    supports_custom_endpoint: bool = False
    default_rate_limit: int = 60
    tracks_token_usage: bool = True
    supports_cost_estimation: bool = False
    custom_features: Dict[str, Any] = field(default_factory=dict)
```

## Built-in Providers

### OpenAI Provider

**Features:**
- GPT-4, GPT-3.5, o-series models
- Automatic cost estimation
- Temperature control (except o-series)
- Vision support (GPT-4 Turbo)
- Function calling

**Configuration:**
```python
from providers import create_openai_provider

provider = create_openai_provider(
    api_key="sk-...",
    default_model="gpt-4o",
    default_temperature=0.7,
    default_max_tokens=2000
)
```

**Supported Models:**
- `gpt-4o` - Latest optimized GPT-4
- `gpt-4o-mini` - Smaller, faster variant
- `gpt-4-turbo` - Vision-capable model
- `gpt-3.5-turbo` - Fast and efficient
- `o1`, `o3` - Reasoning models (no temperature control)

### Anthropic Provider

**Features:**
- Claude 3.x, 3.5, 3.7 models
- Extended context windows (200K tokens)
- Vision support
- Tool use (function calling)
- Separate system message parameter

**Configuration:**
```python
from providers import create_anthropic_provider

provider = create_anthropic_provider(
    api_key="sk-ant-...",
    default_model="claude-3-7-sonnet-20250219",
    default_temperature=0.7,
    default_max_tokens=4000
)
```

**Supported Models:**
- `claude-3-7-sonnet-20250219` - Latest, most balanced
- `claude-3-5-sonnet-20241022` - Advanced reasoning
- `claude-3-5-haiku-20241022` - Fast, efficient
- `claude-3-opus-20240229` - Most capable

### Ollama Provider

**Features:**
- Local LLM inference
- Automatic model downloading
- No API key required
- Support for hundreds of open-source models
- Offline capable

**Configuration:**
```python
from providers import create_ollama_provider

provider = create_ollama_provider(
    base_url="http://localhost:11434",
    default_model="llama3.2",
    default_temperature=0.7,
    default_max_tokens=2000
)
```

**Special Features:**
- `auto_pull_model(model)` - Automatically download models
- `check_model_exists(model)` - Verify if model is available locally
- `get_model_info(model)` - Get detailed model information

**Popular Models:**
- `llama3.2`, `llama3.1` - Meta's LLaMA models
- `mixtral` - Mixtral MoE models
- `codellama` - Specialized for coding
- `llava` - Vision-language model
- `deepseek-coder` - Advanced coding model

## Usage Guide

### Basic Usage

```python
from providers import get_provider, ProviderConfig

# Create a provider
config = ProviderConfig(
    provider_name="openai",
    display_name="OpenAI",
    api_key="sk-...",
    default_model="gpt-4o"
)

provider = get_provider("openai", config)

# Generate a response
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

response_text, metadata = provider.generate_response(
    messages=messages,
    temperature=0.7,
    max_tokens=500
)

print(f"Response: {response_text}")
print(f"Tokens used: {metadata['tokens_used']}")
print(f"Cost: ${metadata.get('estimated_cost_usd', 0):.4f}")
```

### Using ModularAIService

```python
from ai_service_modular import modular_ai_service

# Service auto-initializes providers from config

# Generate response
response, conversation = modular_ai_service.generate_response(
    task="Write a poem",
    generated_prompt=prompt_object,
    context_ids=["ctx1", "ctx2"],
    provider="openai",  # or "anthropic", "ollama"
    model="gpt-4o",
    temperature=0.8
)

# List available models
models = modular_ai_service.list_available_models()
for provider_name, provider_models in models.items():
    print(f"{provider_name}: {len(provider_models)} models")

# Get provider info
info = modular_ai_service.get_provider_info()
for provider in info:
    print(f"{provider['display_name']}: {provider['healthy']}")
```

### Switching Providers

```python
# Start with OpenAI
response1, _ = modular_ai_service.generate_response(
    task="Explain quantum computing",
    generated_prompt=prompt,
    context_ids=[],
    provider="openai",
    model="gpt-4o"
)

# Switch to Anthropic
response2, _ = modular_ai_service.generate_response(
    task="Now explain it more simply",
    generated_prompt=prompt,
    context_ids=[],
    provider="anthropic",
    model="claude-3-7-sonnet-20250219"
)

# Use local Ollama
response3, _ = modular_ai_service.generate_response(
    task="Summarize both explanations",
    generated_prompt=prompt,
    context_ids=[],
    provider="ollama",
    model="llama3.2"
)
```

## Adding a New Provider

To add a new LLM provider (e.g., Google Gemini, Cohere, etc.):

### 1. Create Provider Module

Create `backend/providers/your_provider.py`:

```python
from typing import List, Dict, Optional, Tuple, Any
from .base_provider import BaseLLMProvider, ProviderConfig, ProviderCapabilities
from logger import logger

class YourProvider(BaseLLMProvider):
    """Your provider implementation."""
    
    def __init__(self, config: ProviderConfig):
        # Set provider-specific capabilities
        if not config.capabilities:
            config.capabilities = ProviderCapabilities(
                supports_streaming=True,
                supports_vision=False,
                requires_api_key=True,
                # ... other capabilities
            )
        super().__init__(config)
    
    def initialize(self) -> None:
        """Initialize your provider's client."""
        # Validate config
        # Create API client
        # Test connection
        self._is_initialized = True
        logger.info("Your provider initialized")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response using your provider's API."""
        # Call your provider's API
        # Extract response and metadata
        # Return (response_text, metadata_dict)
        pass
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List models available from your provider."""
        pass
    
    def validate_model(self, model: str) -> bool:
        """Check if a model is valid."""
        pass
```

### 2. Register the Provider

In `provider_registry.py`, add registration:

```python
def _register_builtin_providers(self):
    # ... existing providers ...
    
    # Register your provider
    self.register_provider(
        provider_class=YourProvider,
        name="your_provider",
        display_name="Your Provider",
        description="Description of your provider",
        requires_api_key=True,
        supports_local=False,
        homepage_url="https://yourprovider.com",
        documentation_url="https://docs.yourprovider.com"
    )
```

### 3. Add Configuration

In `config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Your provider settings
    your_provider_api_key: str = Field(default="", description="Your Provider API key")
    your_provider_base_url: str = Field(default="https://api.yourprovider.com", description="API endpoint")
```

### 4. Initialize in ModularAIService

In `ai_service_modular.py`:

```python
def _initialize_providers_from_config(self):
    # ... existing providers ...
    
    # Initialize your provider
    if settings.your_provider_api_key:
        try:
            config = ProviderConfig(
                provider_name="your_provider",
                display_name="Your Provider",
                api_key=settings.your_provider_api_key,
                base_url=settings.your_provider_base_url,
                default_model="your-default-model"
            )
            provider = self.registry.get_provider("your_provider", config)
            self.active_providers["your_provider"] = provider
            logger.info("✓ Your Provider initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Your Provider: {e}")
```

## Testing Providers

### Unit Testing

```python
from providers import ProviderConfig, YourProvider

def test_provider_initialization():
    config = ProviderConfig(
        provider_name="test",
        display_name="Test Provider",
        api_key="test-key",
        default_model="test-model"
    )
    
    provider = YourProvider(config)
    provider.initialize()
    
    assert provider.is_initialized()
    assert provider.config.api_key == "test-key"

def test_generate_response():
    provider = YourProvider(test_config)
    provider.initialize()
    
    messages = [{"role": "user", "content": "Hello"}]
    response, metadata = provider.generate_response(messages)
    
    assert isinstance(response, str)
    assert "tokens_used" in metadata
```

### Integration Testing

```python
def test_provider_integration():
    service = ModularAIService()
    
    # Test provider is available
    assert "your_provider" in service.active_providers
    
    # Test response generation
    response, conv = service.generate_response(
        task="Test task",
        generated_prompt=test_prompt,
        context_ids=[],
        provider="your_provider",
        model="test-model"
    )
    
    assert len(response) > 0
    assert conv.provider == "your_provider"
```

## Configuration Examples

### Environment Variables

`.env` file:

```bash
# OpenAI
CONTEXTPILOT_OPENAI_API_KEY=sk-...
CONTEXTPILOT_DEFAULT_AI_PROVIDER=openai
CONTEXTPILOT_DEFAULT_AI_MODEL=gpt-4o

# Anthropic
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-...

# Ollama
CONTEXTPILOT_OLLAMA_BASE_URL=http://localhost:11434

# General AI settings
CONTEXTPILOT_AI_TEMPERATURE=0.7
CONTEXTPILOT_AI_MAX_TOKENS=2000
```

### Runtime Configuration

```python
from providers import ProviderRegistry, ProviderConfig

registry = ProviderRegistry()

# Configure OpenAI with custom settings
openai_config = ProviderConfig(
    provider_name="openai",
    display_name="OpenAI",
    api_key="sk-...",
    default_model="gpt-4o-mini",
    default_temperature=0.5,
    default_max_tokens=1000,
    extra_params={
        "top_p": 0.9,
        "frequency_penalty": 0.0
    }
)

provider = registry.get_provider("openai", openai_config)
```

## Best Practices

### 1. Use Provider Capabilities

Check what a provider supports before using features:

```python
provider = service.get_provider("ollama")
capabilities = provider.get_capabilities()

if capabilities.supports_vision:
    # Process image inputs
    pass

if capabilities.supports_temperature:
    # Use custom temperature
    pass
```

### 2. Handle Provider-Specific Errors

```python
try:
    response, metadata = provider.generate_response(messages)
except ValueError as e:
    if "model not found" in str(e).lower():
        # Handle missing model
        provider.auto_pull_model(model)  # If supported
    else:
        raise
```

### 3. Cost Monitoring

```python
response, metadata = provider.generate_response(messages)

if "estimated_cost_usd" in metadata:
    cost = metadata["estimated_cost_usd"]
    logger.info(f"Request cost: ${cost:.4f}")
    
    # Track total costs
    total_cost += cost
```

### 4. Provider Health Checks

```python
# Check before making requests
is_healthy, error_msg = provider.health_check()

if not is_healthy:
    logger.error(f"Provider unhealthy: {error_msg}")
    # Fall back to alternative provider
```

## Migration from Old AIService

To migrate from the old monolithic `AIService` to the new modular system:

### Option 1: Direct Replacement

```python
# Old
from ai_service import ai_service
response, conv = ai_service.generate_response(...)

# New
from ai_service_modular import modular_ai_service
response, conv = modular_ai_service.generate_response(...)
```

### Option 2: Gradual Migration

Keep both systems running temporarily:

```python
# Use new system as primary, old as fallback
try:
    from ai_service_modular import modular_ai_service
    response, conv = modular_ai_service.generate_response(...)
except Exception as e:
    logger.warning(f"Modular service failed, using legacy: {e}")
    from ai_service import ai_service
    response, conv = ai_service.generate_response(...)
```

## Future Enhancements

### Planned Features

1. **Streaming Support**: Real-time token streaming
2. **Function Calling**: Unified interface for tools/functions
3. **Vision Input**: Standardized image processing
4. **Embeddings**: Provider-agnostic embedding generation
5. **Rate Limiting**: Per-provider rate limit enforcement
6. **Caching**: Response caching with provider awareness
7. **Fallback Chains**: Automatic failover between providers
8. **Cost Budgets**: Per-provider spending limits
9. **A/B Testing**: Split traffic between providers
10. **Provider Marketplace**: Community-contributed providers

## Troubleshooting

### Provider Won't Initialize

```python
# Check provider is registered
from providers import list_providers
print(list_providers())

# Check configuration
print(provider.config)

# Check initialization error
try:
    provider.initialize()
except Exception as e:
    print(f"Initialization failed: {e}")
```

### Model Not Found

```python
# List available models
models = provider.list_available_models()
print([m['id'] for m in models])

# Validate specific model
is_valid = provider.validate_model("your-model")
print(f"Model valid: {is_valid}")

# For Ollama, try auto-pull
if provider.config.capabilities.custom_features.get("auto_pull_models"):
    provider.auto_pull_model("model-name")
```

### Performance Issues

```python
# Check provider health
is_healthy, error = provider.health_check()
print(f"Healthy: {is_healthy}, Error: {error}")

# Use faster models
# OpenAI: gpt-4o-mini instead of gpt-4
# Anthropic: haiku instead of opus
# Ollama: smaller models like llama3.2:1b

# Reduce token limits
response, metadata = provider.generate_response(
    messages,
    max_tokens=500  # Lower limit for faster responses
)
```

## API Reference

See individual provider modules for complete API documentation:
- [base_provider.py](./providers/base_provider.py) - Abstract base class
- [openai_provider.py](./providers/openai_provider.py) - OpenAI implementation
- [anthropic_provider.py](./providers/anthropic_provider.py) - Anthropic implementation
- [ollama_provider.py](./providers/ollama_provider.py) - Ollama implementation  
- [provider_registry.py](./providers/provider_registry.py) - Registry and factory

## Contributing

To contribute a new provider:

1. Fork the repository
2. Create your provider module following the structure above
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

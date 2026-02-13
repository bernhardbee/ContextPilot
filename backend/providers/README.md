# LLM Provider Modules

This directory contains modular integrations for different LLM providers. Each provider is implemented as a separate module with its own configuration, capabilities, and behavior.

## Structure

```
providers/
├── __init__.py                 # Package initialization and exports
├── base_provider.py            # Abstract base class for all providers
├── provider_registry.py        # Registry and factory for providers
├── openai_provider.py          # OpenAI/GPT integration
├── anthropic_provider.py       # Anthropic/Claude integration
├── ollama_provider.py          # Ollama local LLM integration
└── README.md                   # This file
```

## Quick Start

### Using a Provider Directly

```python
from providers import create_openai_provider

# Create and initialize provider
provider = create_openai_provider(
    api_key="sk-...",
    default_model="gpt-4o"
)

# Generate a response
messages = [
    {"role": "user", "content": "Hello!"}
]
response, metadata = provider.generate_response(messages)
print(response)
```

### Using the Provider Registry

```python
from providers import get_provider, ProviderConfig

# Create configuration
config = ProviderConfig(
    provider_name="anthropic",
    display_name="Anthropic",
    api_key="sk-ant-...",
    default_model="claude-3-7-sonnet-20250219"
)

# Get provider from registry
provider = get_provider("anthropic", config)

# Use the provider
response, metadata = provider.generate_response(messages)
```

### Using ModularAIService

```python
from ai_service_modular import modular_ai_service

# Service automatically initializes all configured providers

# Generate response
response, conversation = modular_ai_service.generate_response(
    task="Your task",
    generated_prompt=prompt_object,
    context_ids=[],
    provider="openai",  # or "anthropic", "ollama"
    model="gpt-4o"
)
```

## Available Providers

### OpenAI
- **Models**: GPT-4, GPT-3.5, o-series
- **Features**: Streaming, function calling, vision, cost estimation
- **Requires**: API key
- **Module**: `openai_provider.py`

### Anthropic
- **Models**: Claude 3.x, 3.5, 3.7
- **Features**: Extended context (200K), vision, tools
- **Requires**: API key
- **Module**: `anthropic_provider.py`

### Ollama
- **Models**: LLaMA, Mixtral, CodeLLaMA, and hundreds more
- **Features**: Local inference, auto-download, offline capable
- **Requires**: Ollama server running
- **Module**: `ollama_provider.py`

## Core Concepts

### BaseLLMProvider

All providers inherit from `BaseLLMProvider` and implement:

- `initialize()` - Set up the provider
- `generate_response()` - Generate AI responses
- `list_available_models()` - Get available models
- `validate_model()` - Check if a model exists

### ProviderConfig

Configuration dataclass with:

- Authentication (API keys, base URLs)
- Default model settings
- Temperature, max tokens, timeouts
- Custom parameters and headers
- Provider capabilities

### ProviderCapabilities

Defines what features a provider supports:

- Streaming, function calling, vision
- Temperature control, token limits
- Local inference, cost estimation
- Custom features per provider

### ProviderRegistry

Central registry that:

- Registers all available providers
- Creates provider instances
- Manages provider metadata
- Provides discovery functionality

## Adding a New Provider

See [PROVIDER_ARCHITECTURE.md](../PROVIDER_ARCHITECTURE.md#adding-a-new-provider) for详细步骤.

Quick overview:

1. Create `your_provider.py` inheriting from `BaseLLMProvider`
2. Implement required methods
3. Register in `provider_registry.py`
4. Add configuration in `config.py`
5. Initialize in `ai_service_modular.py`

## Examples

### List All Available Models

```python
from ai_service_modular import modular_ai_service

models = modular_ai_service.list_available_models()
for provider, provider_models in models.items():
    print(f"\n{provider}:")
    for model in provider_models:
        print(f"  - {model['id']}: {model['name']}")
```

### Check Provider Health

```python
provider = modular_ai_service.get_provider("openai")
is_healthy, error_msg = provider.health_check()
if is_healthy:
    print("Provider is healthy")
else:
    print(f"Provider error: {error_msg}")
```

### Get Provider Capabilities

```python
provider = modular_ai_service.get_provider("anthropic")
caps = provider.get_capabilities()

print(f"Supports streaming: {caps.supports_streaming}")
print(f"Supports vision: {caps.supports_vision}")
print(f"Requires API key: {caps.requires_api_key}")
```

### Use Provider-Specific Features

```python
# Ollama auto-pull
ollama = modular_ai_service.get_provider("ollama")
if not ollama.check_model_exists("llama3.2"):
    ollama.auto_pull_model("llama3.2")

# OpenAI cost estimation
openai = modular_ai_service.get_provider("openai")
_, metadata = openai.generate_response(messages, model="gpt-4o")
print(f"Cost: ${metadata['estimated_cost_usd']:.4f}")
```

## Configuration

### Environment Variables

```bash
# OpenAI
CONTEXTPILOT_OPENAI_API_KEY=sk-...
CONTEXTPILOT_DEFAULT_AI_PROVIDER=openai
CONTEXTPILOT_DEFAULT_AI_MODEL=gpt-4o

# Anthropic
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-...

# Ollama
CONTEXTPILOT_OLLAMA_BASE_URL=http://localhost:11434

# Settings
CONTEXTPILOT_AI_TEMPERATURE=0.7
CONTEXTPILOT_AI_MAX_TOKENS=2000
```

### Programmatic Configuration

```python
from providers import ProviderConfig, ProviderCapabilities

config = ProviderConfig(
    provider_name="openai",
    display_name="OpenAI",
    api_key="sk-...",
    default_model="gpt-4o",
    default_temperature=0.8,
    default_max_tokens=3000,
    extra_params={
        "top_p": 0.9,
        "frequency_penalty": 0.1
    }
)
```

## Testing

### Unit Tests

```python
import pytest
from providers import ProviderConfig, OpenAIProvider

def test_provider_init():
    config = ProviderConfig(
        provider_name="openai",
        display_name="OpenAI",
        api_key="test-key",
        default_model="gpt-4o"
    )
    provider = OpenAIProvider(config)
    assert provider.config.api_key == "test-key"

def test_validate_model():
    provider = OpenAIProvider(config)
    assert provider.validate_model("gpt-4o")
    assert not provider.validate_model("invalid-model")
```

### Integration Tests

```python
def test_generate_response():
    from ai_service_modular import modular_ai_service
    
    response, conv = modular_ai_service.generate_response(
        task="Test",
        generated_prompt=test_prompt,
        context_ids=[],
        provider="openai",
        model="gpt-4o-mini"
    )
    
    assert len(response) > 0
    assert conv.provider == "openai"
```

## Best Practices

1. **Always check capabilities** before using features
2. **Handle provider-specific errors** appropriately
3. **Monitor costs** when using paid APIs
4. **Use health checks** before important operations
5. **Cache provider instances** when possible
6. **Validate models** before making requests
7. **Set appropriate timeouts** for your use case

## Documentation

- **Architecture Overview**: [PROVIDER_ARCHITECTURE.md](../PROVIDER_ARCHITECTURE.md)
- **Base Provider API**: [base_provider.py](./base_provider.py)
- **OpenAI Provider**: [openai_provider.py](./openai_provider.py)
- **Anthropic Provider**: [anthropic_provider.py](./anthropic_provider.py)
- **Ollama Provider**: [ollama_provider.py](./ollama_provider.py)
- **Registry & Factory**: [provider_registry.py](./provider_registry.py)

## Troubleshooting

### "Provider not initialized"
```python
provider = service.get_provider("openai")
if not provider.is_initialized():
    provider.initialize()
```

### "Model not found"
```python
models = provider.list_available_models()
print([m['id'] for m in models])
```

### "API key missing"
```python
config.api_key = "your-api-key"
provider = OpenAIProvider(config)
provider.initialize()
```

### Ollama connection issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Test with a model
ollama run llama3.2 "Hello"
```

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review existing provider implementations
- See [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

See [LICENSE](../LICENSE) file in the root directory.

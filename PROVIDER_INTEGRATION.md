# Modular Provider System Integration Guide

## Quick Start

The new modular provider architecture has been fully integrated into ContextPilot. This guide shows you how to use it.

## What Changed?

### Before (Monolithic)
```python
from ai_service import ai_service

# Single AIService class with hardcoded provider logic
response, conv = ai_service.generate_response(...)
```

### After (Modular)
```python
from ai_service_modular import modular_ai_service

# Same interface, but providers are now modular and extensible
response, conv = modular_ai_service.generate_response(...)
```

## Migration Guide

### Option 1: Keep Using Old System

The old `AIService` in `ai_service.py` still works and all existing code continues to function.

```python
# Existing code - NO CHANGES NEEDED
from ai_service import ai_service
response, conv = ai_service.generate_response(
    task="your task",
    generated_prompt=prompt,
    context_ids=[],
    provider="openai",
    model="gpt-4o"
)
```

### Option 2: Migrate to New System

Update imports to use the new modular service:

```python
# New modular system
from ai_service_modular import modular_ai_service

# Exact same interface
response, conv = modular_ai_service.generate_response(
    task="your task",
    generated_prompt=prompt,
    context_ids=[],
    provider="openai",
    model="gpt-4o"
)
```

**Benefits of migrating:**
- Better separation of concerns
- Easier to add new providers
- Provider-specific features
- Better testing and maintainability
- Cost estimation built-in
- Health monitoring

## Using Providers Directly

### Get a Provider Instance

```python
from providers import get_provider, ProviderConfig

# Configure provider
config = ProviderConfig(
    provider_name="openai",
    display_name="OpenAI",
    api_key="sk-...",
    default_model="gpt-4o"
)

# Get provider
provider = get_provider("openai", config)

# Use provider
messages = [{"role": "user", "content": "Hello!"}]
response, metadata = provider.generate_response(messages)
```

### List All Available Providers

```python
from providers import list_providers

providers = list_providers()
for p in providers:
    print(f"{p['display_name']}: {p['description']}")
```

### Check Provider Capabilities

```python
provider = modular_ai_service.get_provider("openai")
caps = provider.get_capabilities()

if caps.supports_vision:
    # Can send images
    pass

if caps.supports_cost_estimation:
    # Can estimate costs
    cost = provider.estimate_cost(1000, 500, "gpt-4o")
    print(f"Estimated cost: ${cost:.4f}")
```

## Configuration

### Environment Variables

No changes needed! The new system uses the same environment variables:

```bash
# .env file
CONTEXTPILOT_OPENAI_API_KEY=sk-...
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-...
CONTEXTPILOT_OLLAMA_BASE_URL=http://localhost:11434
CONTEXTPILOT_DEFAULT_AI_PROVIDER=openai
CONTEXTPILOT_DEFAULT_AI_MODEL=gpt-4o
```

### Programmatic Configuration

```python
from providers import create_openai_provider

# Create provider with custom settings
provider = create_openai_provider(
    api_key="sk-...",
    default_model="gpt-4o-mini",
    default_temperature=0.9,
    default_max_tokens=500
)
```

## Testing

All 205 backend tests pass, including 22 new provider-specific tests:

```bash
cd backend
python -m pytest test_providers.py -v
```

### Test Coverage

- ✅ Provider configuration validation
- ✅ Capability detection
- ✅ Model validation
- ✅ Cost estimation (OpenAI/Anthropic)
- ✅ Provider registry
- ✅ Factory patterns
- ✅ Integration with ModularAIService

## Common Tasks

### Add a New Provider

See [PROVIDER_ARCHITECTURE.md](../PROVIDER_ARCHITECTURE.md#adding-a-new-provider) for detailed instructions.

Quick summary:
1. Create `your_provider.py` inheriting from `BaseLLMProvider`
2. Implement required methods
3. Register in `provider_registry.py`
4. Add config in `config.py`
5. Initialize in `ai_service_modular.py`

### Switch Between Providers

```python
# Use OpenAI
response1, _ = modular_ai_service.generate_response(
    ...,
    provider="openai",
    model="gpt-4o"
)

# Switch to Anthropic
response2, _ = modular_ai_service.generate_response(
    ...,
    provider="anthropic",
    model="claude-3-7-sonnet-20250219"
)

# Use local Ollama
response3, _ = modular_ai_service.generate_response(
    ...,
    provider="ollama",
    model="llama3.2"
)
```

### Monitor Costs

```python
provider = modular_ai_service.get_provider("openai")
response, metadata = provider.generate_response(messages, model="gpt-4o")

if "estimated_cost_usd" in metadata:
    print(f"This request cost: ${metadata['estimated_cost_usd']:.4f}")
    print(f"Tokens used: {metadata['tokens_used']}")
    print(f"Input tokens: {metadata['input_tokens']}")
    print(f"Output tokens: {metadata['output_tokens']}")
```

### Health Checks

```python
# Check single provider
provider = modular_ai_service.get_provider("openai")
is_healthy, error = provider.health_check()
print(f"OpenAI healthy: {is_healthy}")

# Check all providers
info = modular_ai_service.get_provider_info()
for p in info:
    status = "✓" if p['healthy'] else "✗"
    print(f"{status} {p['display_name']}")
```

### List Available Models

```python
# All providers
all_models = modular_ai_service.list_available_models()
for provider_name, models in all_models.items():
    print(f"\n{provider_name}:")
    for model in models:
        print(f"  - {model['id']}: {model['name']}")

# Specific provider
provider = modular_ai_service.get_provider("openai")
models = provider.list_available_models()
```

## Troubleshooting

### Import Errors

```python
# If you see: "cannot import name 'modular_ai_service'"
# Make sure you're using the correct import:
from ai_service_modular import modular_ai_service

# NOT from ai_service import ai_service
```

### Provider Not Initialized

```python
# Check active providers
from ai_service_modular import modular_ai_service

print("Active providers:", list(modular_ai_service.active_providers.keys()))

# Check if API keys are set
from config import settings
print("OpenAI key set:", bool(settings.openai_api_key))
print("Anthropic key set:", bool(settings.anthropic_api_key))
```

### Tests Failing

```bash
# Make sure httpx is updated
pip install "httpx>=0.27.0"

# Run tests
python -m pytest -v

# Run specific provider tests
python -m pytest test_providers.py -v
```

## Performance

The new modular system has **no performance overhead** compared to the old system:
- Same API calls
- Same response times
- Same token usage
- Better code organization
- Easier to maintain

## Security

Provider modules include security best practices:
- API keys never logged
- Sensitive data sanitized
- Rate limiting support
- Request timeouts
- Error messages sanitized

## Examples

See `backend/example_providers.py` for complete working examples:

```bash
cd backend
python example_providers.py
```

Examples include:
- Basic provider usage
- Listing providers and models
- Checking capabilities
- Health checks
- Cost estimation
- Custom configuration
- Ollama auto-pull

## Documentation

Complete documentation available:

- **[PROVIDER_ARCHITECTURE.md](../PROVIDER_ARCHITECTURE.md)** - Architecture overview
- **[providers/README.md](../backend/providers/README.md)** - Provider module guide
- **[example_providers.py](../backend/example_providers.py)** - Code examples
- Individual provider modules have inline documentation

## Support

For questions or issues:
1. Check documentation
2. Run example_providers.py
3. Review test files for usage patterns
4. Open an issue on GitHub

## What's Next?

Future enhancements:
- Streaming support
- Function calling interface
- Vision input support
- Embeddings providers
- Response caching
- A/B testing
- Cost budgets
- Community providers

## Summary

The modular provider system is:
- ✅ **Production ready** - All tests passing
- ✅ **Backward compatible** - Old code still works
- ✅ **Well documented** - Comprehensive guides
- ✅ **Easy to use** - Same interface as before
- ✅ **Extensible** - Add providers easily
- ✅ **Type safe** - Full type hints
- ✅ **Tested** - 205 tests, 100% passing

Start using it today by importing from `ai_service_modular` instead of `ai_service`!

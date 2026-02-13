"""
Example: Using the Modular Provider System

This script demonstrates how to use the new modular LLM provider architecture.
"""
import os
from providers import (
    ProviderConfig,
    create_openai_provider,
    create_anthropic_provider,
    create_ollama_provider,
    list_providers
)


def example_1_basic_usage():
    """Example 1: Basic usage with OpenAI"""
    print("=" * 60)
    print("Example 1: Basic Provider Usage")
    print("=" * 60)
    
    # Create provider
    provider = create_openai_provider(
        api_key=os.getenv("OPENAI_API_KEY", "sk-test"),
        default_model="gpt-4o-mini"
    )
    
    # Generate a response
    messages = [
        {"role": "user", "content": "What is 2+2?"}
    ]
    
    try:
        response, metadata = provider.generate_response(messages)
        print(f"Response: {response}")
        print(f"Model: {metadata['model_used']}")
        print(f"Tokens: {metadata['tokens_used']}")
        if 'estimated_cost_usd' in metadata:
            print(f"Cost: ${metadata['estimated_cost_usd']:.4f}")
    except Exception as e:
        print(f"Error: {e}")


def example_2_list_providers():
    """Example 2: List all available providers"""
    print("\n" + "=" * 60)
    print("Example 2: List Available Providers")
    print("=" * 60)
    
    providers = list_providers()
    for provider_info in providers:
        print(f"\n{provider_info['display_name']} ({provider_info['name']})")
        print(f"  Description: {provider_info['description']}")
        print(f"  Requires API Key: {provider_info['requires_api_key']}")
        print(f"  Local: {provider_info['supports_local']}")
        print(f"  Initialized: {provider_info['initialized']}")


def example_3_list_models():
    """Example 3: List available models for a provider"""
    print("\n" + "=" * 60)
    print("Example 3: List Available Models")
    print("=" * 60)
    
    try:
        # Create OpenAI provider
        provider = create_openai_provider(
            api_key=os.getenv("OPENAI_API_KEY", "sk-test"),
            default_model="gpt-4o"
        )
        
        models = provider.list_available_models()
        print(f"\n{provider.config.display_name} Models:")
        for model in models[:5]:  # Show first 5
            print(f"  - {model['id']}: {model['name']}")
            print(f"    Context: {model['context_window']} tokens")
            print(f"    Capabilities: {', '.join(model['capabilities'])}")
    except Exception as e:
        print(f"Error: {e}")


def example_4_provider_capabilities():
    """Example 4: Check provider capabilities"""
    print("\n" + "=" * 60)
    print("Example 4: Provider Capabilities")
    print("=" * 60)
    
    providers_to_check = [
        ("openai", os.getenv("OPENAI_API_KEY")),
        ("anthropic", os.getenv("ANTHROPIC_API_KEY")),
        ("ollama", None)
    ]
    
    for provider_name, api_key in providers_to_check:
        try:
            if provider_name == "openai" and api_key:
                provider = create_openai_provider(api_key=api_key)
            elif provider_name == "anthropic" and api_key:
                provider = create_anthropic_provider(api_key=api_key)
            elif provider_name == "ollama":
                provider = create_ollama_provider()
            else:
                continue
            
            caps = provider.get_capabilities()
            print(f"\n{provider.config.display_name}:")
            print(f"  Streaming: {caps.supports_streaming}")
            print(f"  Function Calling: {caps.supports_function_calling}")
            print(f"  Vision: {caps.supports_vision}")
            print(f"  System Messages: {caps.supports_system_messages}")
            print(f"  Temperature: {caps.supports_temperature}")
            print(f"  Cost Estimation: {caps.supports_cost_estimation}")
            
            if caps.custom_features:
                print(f"  Custom Features: {list(caps.custom_features.keys())}")
        
        except Exception as e:
            print(f"\n{provider_name}: {e}")


def example_5_health_check():
    """Example 5: Health check providers"""
    print("\n" + "=" * 60)
    print("Example 5: Provider Health Checks")
    print("=" * 60)
    
    providers_to_check = [
        ("openai", os.getenv("OPENAI_API_KEY")),
        ("anthropic", os.getenv("ANTHROPIC_API_KEY")),
        ("ollama", None)
    ]
    
    for provider_name, api_key in providers_to_check:
        try:
            if provider_name == "openai" and api_key:
                provider = create_openai_provider(api_key=api_key)
            elif provider_name == "anthropic" and api_key:
                provider = create_anthropic_provider(api_key=api_key)
            elif provider_name == "ollama":
                provider = create_ollama_provider()
            else:
                print(f"\n{provider_name}: Skipped (no API key)")
                continue
            
            is_healthy, error_msg = provider.health_check()
            status = "✓ Healthy" if is_healthy else f"✗ Unhealthy: {error_msg}"
            print(f"\n{provider.config.display_name}: {status}")
        
        except Exception as e:
            print(f"\n{provider_name}: Error - {e}")


def example_6_modular_ai_service():
    """Example 6: Using ModularAIService"""
    print("\n" + "=" * 60)
    print("Example 6: ModularAIService")
    print("=" * 60)
    
    try:
        from ai_service_modular import modular_ai_service
        from models import GeneratedPrompt
        
        # Get provider info
        info = modular_ai_service.get_provider_info()
        print("\nActive Providers:")
        for provider in info:
            status = "✓" if provider['healthy'] else "✗"
            print(f"  {status} {provider['display_name']}: {provider['default_model']}")
        
        # List models from all providers
        all_models = modular_ai_service.list_available_models()
        print(f"\nTotal Providers: {len(all_models)}")
        for provider_name, models in all_models.items():
            print(f"  {provider_name}: {len(models)} models")
        
        # Example: Generate response (requires proper setup)
        # prompt = GeneratedPrompt(...)
        # response, conv = modular_ai_service.generate_response(
        #     task="Test task",
        #     generated_prompt=prompt,
        #     context_ids=[],
        #     provider="openai",
        #     model="gpt-4o-mini"
        # )
        
    except Exception as e:
        print(f"ModularAIService Error: {e}")


def example_7_custom_configuration():
    """Example 7: Custom provider configuration"""
    print("\n" + "=" * 60)
    print("Example 7: Custom Configuration")
    print("=" * 60)
    
    # Create custom configuration
    config = ProviderConfig(
        provider_name="openai",
        display_name="My Custom OpenAI",
        api_key=os.getenv("OPENAI_API_KEY", "sk-test"),
        default_model="gpt-4o-mini",
        default_temperature=0.9,  # More creative
        default_max_tokens=500,    # Shorter responses
        extra_params={
            "top_p": 0.95,
            "frequency_penalty": 0.5
        }
    )
    
    print(f"\nConfiguration:")
    print(f"  Provider: {config.provider_name}")
    print(f"  Model: {config.default_model}")
    print(f"  Temperature: {config.default_temperature}")
    print(f"  Max Tokens: {config.default_max_tokens}")
    print(f"  Extra Params: {config.extra_params}")
    
    try:
        from providers import get_provider
        provider = get_provider("openai", config)
        print(f"\n✓ Provider created with custom config")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_8_ollama_auto_pull():
    """Example 8: Ollama auto-pull feature"""
    print("\n" + "=" * 60)
    print("Example 8: Ollama Auto-Pull")
    print("=" * 60)
    
    try:
        provider = create_ollama_provider(
            base_url="http://localhost:11434",
            default_model="llama3.2"
        )
        
        # Check if model exists
        model_name = "llama3.2"
        exists = provider.check_model_exists(model_name)
        print(f"\nModel '{model_name}' exists: {exists}")
        
        if not exists:
            print(f"Attempting to pull '{model_name}'...")
            success = provider.auto_pull_model(model_name)
            if success:
                print(f"✓ Model pulled successfully")
            else:
                print(f"✗ Failed to pull model")
        
        # List available models
        models = provider.list_available_models()
        print(f"\nAvailable Ollama models: {len(models)}")
        for model in models[:5]:
            print(f"  - {model['id']}")
    
    except Exception as e:
        print(f"Ollama Error: {e}")
        print("Make sure Ollama is installed and running:")
        print("  - Install: https://ollama.ai")
        print("  - Start: ollama serve")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MODULAR LLM PROVIDER EXAMPLES")
    print("=" * 60)
    
    # Run examples
    example_2_list_providers()
    example_4_provider_capabilities()
    example_5_health_check()
    example_7_custom_configuration()
    
    # These require API keys
    if os.getenv("OPENAI_API_KEY"):
        example_1_basic_usage()
        example_3_list_models()
    else:
        print("\n⚠️  Set OPENAI_API_KEY to run generation examples")
    
    # This requires Ollama
    example_8_ollama_auto_pull()
    
    # This requires full app setup
    example_6_modular_ai_service()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

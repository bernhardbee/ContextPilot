#!/usr/bin/env python3
"""
Quick demo of the dynamic model discovery system for ContextPilot.
"""

import json
from pathlib import Path

def main():
    """Demo the dynamic model system."""
    print("🧭 ContextPilot Dynamic Model Discovery Demo")
    print("=" * 50)
    
    # Show discovered models
    models_file = Path("frontend/src/model_options.json")
    if models_file.exists():
        with open(models_file, 'r') as f:
            models = json.load(f)
        
        print("\n📊 Currently Available Models:")
        print("-" * 30)
        
        for provider, model_list in models.items():
            print(f"\n{provider.upper()}:")
            if model_list:
                for model in model_list:
                    # Add friendly names for common models
                    friendly_name = model
                    if 'gpt-4o' in model:
                        friendly_name += " (Latest GPT-4)"
                    elif 'claude-3-5-sonnet' in model:
                        friendly_name += " (Latest Claude)"
                    elif 'llama' in model.lower():
                        friendly_name += " (Local)"
                    
                    print(f"  ✅ {friendly_name}")
            else:
                print("  (no models available)")
        
        # Show totals
        total = sum(len(models) for models in models.values())
        print(f"\n📈 Total: {total} models across {len(models)} providers")
        
        # Show cache info
        cache_file = Path("available_models_cache.json")
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            print(f"📅 Last updated: {cache.get('timestamp', 'unknown')}")
        
    else:
        print("❌ No models file found. Run 'python3 discover_models.py' first.")
        return
    
    print(f"\n💡 Key Features:")
    print(f"  • Automatic model discovery from all providers")
    print(f"  • 24-hour caching for performance") 
    print(f"  • Fallback models when APIs unavailable")
    print(f"  • Local Ollama model detection")
    print(f"  • Startup integration with backend")
    
    print(f"\n🔄 To refresh models:")
    print(f"  • Manual: python3 discover_models.py")
    print(f"  • Force: python3 refresh_models.py --force")
    print(f"  • Automatic: Runs when backend starts (if cache stale)")

if __name__ == "__main__":
    main()
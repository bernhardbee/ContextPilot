#!/usr/bin/env python3
"""
Startup integration for ContextPilot model discovery.
This can be called from the backend at startup to ensure fresh model lists.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

def should_refresh_models(max_age_hours: int = 24) -> bool:
    """Check if models should be refreshed based on cache age."""
    cache_file = Path(__file__).parent / "available_models_cache.json"
    
    if not cache_file.exists():
        return True
        
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            
        cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
        if datetime.now() - cache_time > timedelta(hours=max_age_hours):
            return True
            
    except (json.JSONDecodeError, KeyError, ValueError):
        return True
        
    return False

def refresh_models_if_needed(max_age_hours: int = 24, force: bool = False) -> bool:
    """Refresh models if cache is stale or force is True."""
    if force or should_refresh_models(max_age_hours):
        print("🔄 Refreshing model list...")
        
        try:
            # Import and run model discovery
            sys.path.insert(0, str(Path(__file__).parent))
            from discover_models import ModelDiscoveryService
            
            discovery = ModelDiscoveryService()
            models = discovery.discover_all_models()
            
            discovery.update_frontend_models(models)
            discovery.update_backend_validation(models)
            
            total_models = sum(len(model_list) for model_list in models.values())
            print(f"✅ Model refresh complete! {total_models} models available")
            return True
            
        except Exception as e:
            print(f"⚠️  Model refresh failed: {e}")
            return False
    else:
        print("📋 Model cache is fresh, skipping refresh")
        return True

def main():
    """Command line interface for model refresh."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ContextPilot Model Refresh")
    parser.add_argument("--force", action="store_true", help="Force refresh even if cache is fresh")
    parser.add_argument("--max-age", type=int, default=24, help="Maximum cache age in hours (default: 24)")
    
    args = parser.parse_args()
    
    success = refresh_models_if_needed(args.max_age, args.force)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
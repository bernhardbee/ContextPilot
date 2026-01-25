#!/usr/bin/env python3
"""
Dynamic model discovery service for ContextPilot.
Fetches available models from each AI provider and updates the system accordingly.
"""

import json
import requests
import subprocess
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from config import settings
    from logger import logger
except ImportError:
    # Fallback for when backend modules aren't available
    print("⚠️  Backend modules not available, using basic configuration")
    
    class Settings:
        openai_api_key = os.environ.get('OPENAI_API_KEY', '')
        ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    settings = Settings()


class ModelDiscoveryService:
    """Service to discover available models from AI providers."""
    
    def __init__(self):
        self.cache_file = Path(__file__).parent / "available_models_cache.json"
        self.cache_ttl_hours = 24  # Cache models for 24 hours
        
    def discover_all_models(self) -> Dict[str, List[str]]:
        """Discover available models from all providers."""
        print("🔍 Discovering available models from all providers...")
        
        models = {
            "openai": [],
            "anthropic": [],
            "ollama": []
        }
        
        # Try to load from cache first
        cached_models = self._load_cache()
        if cached_models:
            print("📋 Using cached model list (still fresh)")
            return cached_models
        
        # Discover OpenAI models
        try:
            models["openai"] = self._discover_openai_models()
        except Exception as e:
            print(f"⚠️  OpenAI model discovery failed: {e}")
            models["openai"] = self._get_fallback_openai_models()
            
        # Discover Anthropic models (maintained list since no public API)
        models["anthropic"] = self._get_anthropic_models()
        
        # Discover Ollama models
        try:
            models["ollama"] = self._discover_ollama_models()
        except Exception as e:
            print(f"⚠️  Ollama model discovery failed: {e}")
            models["ollama"] = []
            
        # Cache the results
        self._save_cache(models)
        
        return models
    
    def _discover_openai_models(self) -> List[str]:
        """Discover available OpenAI models via API."""
        if not settings.openai_api_key:
            print("⚠️  No OpenAI API key configured, using fallback models")
            return self._get_fallback_openai_models()
            
        print("🔍 Fetching OpenAI models...")
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            data = response.json()
            
            # Filter to chat models only and sort by capability/recency
            chat_models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                
                # Filter for chat models - future-proof for any GPT version
                # Include: gpt-*, chatgpt, o1, o3 (reasoning models)
                if (model_id.startswith("gpt-") or 
                    model_id.startswith("chatgpt") or
                    model_id.startswith("o1") or
                    model_id.startswith("o3")):
                    chat_models.append(model_id)
            
            # Sort models by preference (newer/better models first)
            def model_priority(model_id):
                # Extract version number for GPT models (e.g., "5" from "gpt-5")
                import re
                gpt_match = re.match(r'gpt-(\d+)', model_id)
                if gpt_match:
                    version = int(gpt_match.group(1))
                    # Higher version = higher priority (lower number)
                    base_priority = (10 - version) * 10  # gpt-5 = 50, gpt-4 = 60, etc.
                    # Prefer 'o' variants and turbo
                    if 'o' in model_id and 'turbo' not in model_id:
                        return base_priority - 2
                    elif 'turbo' in model_id:
                        return base_priority - 1
                    else:
                        return base_priority
                # Reasoning models (o1, o3) - high priority
                elif model_id.startswith(('o1', 'o3')):
                    return 5
                # ChatGPT models
                elif 'chatgpt' in model_id:
                    return 100
                else:
                    return 200
            
            chat_models.sort(key=model_priority)
            print(f"✅ Found {len(chat_models)} OpenAI chat models")
            return chat_models
            
        except Exception as e:
            raise Exception(f"Failed to fetch OpenAI models: {e}")
    
    def _get_fallback_openai_models(self) -> List[str]:
        """Fallback OpenAI models when API discovery fails."""
        # Note: Keep this updated with latest stable models
        return [
            # Latest models (update as new versions release)
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            # Add gpt-5* models here when they become available
        ]
    
    def _get_anthropic_models(self) -> List[str]:
        """Get Anthropic models (maintained list since no public API)."""
        print("📋 Using maintained Anthropic model list")
        # Note: Update this list when new Claude versions are released
        # Format: claude-{version}-{variant}-{date}
        return [
            # Claude 4 series (add when available)
            # "claude-4-opus-YYYYMMDD",
            # "claude-4-sonnet-YYYYMMDD",
            
            # Claude 3.5 series
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            
            # Claude 3 series
            "claude-3-opus-20240229", 
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    def _discover_ollama_models(self) -> List[str]:
        """Discover locally installed Ollama models."""
        print("🔍 Checking Ollama models...")
        
        try:
            # Try API approach first
            url = f"{settings.ollama_base_url}/api/tags"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                print(f"✅ Found {len(models)} Ollama models via API")
                return sorted(models)
        except:
            pass
            
        # Fallback to CLI approach
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]  # First column is model name
                        models.append(model_name)
                
                print(f"✅ Found {len(models)} Ollama models via CLI")
                return sorted(models)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("⚠️  Ollama not available or no models installed")
        return []
    
    def _load_cache(self) -> Optional[Dict[str, List[str]]]:
        """Load cached models if still fresh."""
        if not self.cache_file.exists():
            return None
            
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
            if datetime.now() - cache_time > timedelta(hours=self.cache_ttl_hours):
                print("📋 Model cache expired, refreshing...")
                return None
                
            return cache_data.get("models", {})
            
        except Exception:
            return None
    
    def _save_cache(self, models: Dict[str, List[str]]) -> None:
        """Save models to cache."""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "models": models
        }
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"💾 Cached models to {self.cache_file}")
        except Exception as e:
            print(f"⚠️  Failed to cache models: {e}")
    
    def update_frontend_models(self, models: Dict[str, List[str]]) -> None:
        """Update frontend model options."""
        frontend_file = Path(__file__).parent / "frontend" / "src" / "model_options.json"
        
        try:
            with open(frontend_file, 'w') as f:
                json.dump(models, f, indent=2)
            print(f"✅ Updated frontend model options: {frontend_file}")
        except Exception as e:
            print(f"⚠️  Failed to update frontend: {e}")
    
    def update_backend_validation(self, models: Dict[str, List[str]]) -> None:
        """Update backend model validation."""
        validation_file = Path(__file__).parent / "backend" / "valid_models.json"
        
        try:
            with open(validation_file, 'w') as f:
                json.dump(models, f, indent=2)
            print(f"✅ Updated backend model validation: {validation_file}")
        except Exception as e:
            print(f"⚠️  Failed to update backend validation: {e}")


def main():
    """Main discovery process."""
    print("🧭 ContextPilot Model Discovery Service")
    print("=" * 50)
    
    discovery = ModelDiscoveryService()
    
    # Discover models
    models = discovery.discover_all_models()
    
    # Display results
    print("\n📊 Model Discovery Results:")
    print("=" * 30)
    
    for provider, model_list in models.items():
        print(f"\n{provider.upper()}:")
        if model_list:
            for i, model in enumerate(model_list, 1):
                print(f"  {i:2}. {model}")
        else:
            print("  (no models available)")
    
    # Update system files
    print("\n🔄 Updating system configuration...")
    discovery.update_frontend_models(models)
    discovery.update_backend_validation(models)
    
    # Generate summary
    total_models = sum(len(model_list) for model_list in models.values())
    print(f"\n✅ Discovery complete! Found {total_models} total models")
    print(f"   OpenAI: {len(models['openai'])} models")
    print(f"   Anthropic: {len(models['anthropic'])} models") 
    print(f"   Ollama: {len(models['ollama'])} models")
    
    print("\n💡 Next steps:")
    print("   • Restart backend to use updated model validation")
    print("   • Restart frontend to show new model options")
    print("   • Re-run this script daily or when adding new models")


if __name__ == "__main__":
    main()
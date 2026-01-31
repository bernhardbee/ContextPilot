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
        self._load_api_key_from_cache()
        
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
            
        # Discover Anthropic models
        try:
            models["anthropic"] = self._discover_anthropic_models()
        except Exception as e:
            print(f"⚠️  Anthropic model discovery failed: {e}")
            models["anthropic"] = self._get_fallback_anthropic_models()
        
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
                # Extract version number for GPT models (e.g., "5.2" from "gpt-5.2", "5" from "gpt-5")
                import re
                gpt_match = re.match(r'gpt-(\d+)(?:\.(\d+))?', model_id)
                if gpt_match:
                    major_version = int(gpt_match.group(1))
                    minor_version = int(gpt_match.group(2)) if gpt_match.group(2) else 0
                    # Higher version = higher priority (lower number)
                    # Use float-like priority: gpt-5.2 = 47.8, gpt-5 = 50, gpt-4 = 60
                    base_priority = (10 - major_version) * 10 - (minor_version * 0.2)
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
            
            # Check for newer models before filtering
            import re
            all_versions = {}
            for model_id in chat_models:
                gpt_match = re.match(r'gpt-(\d+)(?:\.(\d+))?', model_id)
                if gpt_match:
                    major = int(gpt_match.group(1))
                    minor = int(gpt_match.group(2)) if gpt_match.group(2) else 0
                    version_key = f"{major}.{minor}"
                    if version_key not in all_versions:
                        all_versions[version_key] = []
                    all_versions[version_key].append(model_id)
            
            # Filter to keep only best general models: gpt-5.2, gpt-4o, and reasoning models
            print(f"🎯 Filtering to best general models: GPT-5.2, GPT-4o variants, and reasoning models")
            
            filtered_models = []
            for model_id in chat_models:
                # Keep gpt-5.2 variants
                if model_id.startswith('gpt-5.2'):
                    filtered_models.append(model_id)
                # Keep gpt-4o variants
                elif model_id.startswith('gpt-4o'):
                    filtered_models.append(model_id)
                # Keep reasoning models (o1, o3)
                elif model_id.startswith(('o1', 'o3')):
                    filtered_models.append(model_id)
                # Keep chatgpt models
                elif model_id.startswith('chatgpt'):
                    filtered_models.append(model_id)
            
            # Check for newer versions that were filtered out
            newer_versions = []
            for version_key in all_versions.keys():
                try:
                    major, minor = map(int, version_key.split('.'))
                    # Check if this is newer than gpt-5.2 (major > 5, or major == 5 and minor > 2)
                    if major > 5 or (major == 5 and minor > 2):
                        newer_versions.append((version_key, all_versions[version_key]))
                except:
                    pass
            
            if newer_versions:
                print("\n" + "⚠️ " * 20)
                print("🆕 NEWER MODELS AVAILABLE BUT NOT INCLUDED:")
                print("=" * 60)
                for version, models in sorted(newer_versions, reverse=True):
                    print(f"\n  GPT-{version} series ({len(models)} models):")
                    for model in models[:3]:  # Show first 3 examples
                        print(f"    • {model}")
                    if len(models) > 3:
                        print(f"    ... and {len(models) - 3} more")
                print("\n💡 Update the filter in discover_models.py to include these")
                print("=" * 60 + "\n")
            
            chat_models = filtered_models

            
            print(f"✅ Found {len(chat_models)} OpenAI chat models")
            return chat_models
            
        except Exception as e:
            raise Exception(f"Failed to fetch OpenAI models: {e}")
    
    def _get_fallback_openai_models(self) -> List[str]:
        """Fallback OpenAI models when API discovery fails."""
        print("\n" + "="*60)
        print("⚠️  WARNING: Using fallback OpenAI model list!")
        print("="*60)
        print("Configure CONTEXTPILOT_OPENAI_API_KEY to discover models")
        print("from the OpenAI API automatically. The fallback list may")
        print("be outdated and missing newer models.")
        print("="*60 + "\n")
        
        # Note: Keep this updated with latest stable models
        return [
            # GPT-5 series (latest generation)
            "gpt-5.2",
            "gpt-5",
            "gpt-5-turbo",
            # GPT-4 series
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            # GPT-3.5 series
            "gpt-3.5-turbo",
        ]
    
    def _discover_anthropic_models(self) -> List[str]:
        """Discover Anthropic models via API."""
        print("🔍 Discovering Anthropic models...")
        
        # Get API key
        anthropic_key = os.environ.get('CONTEXTPILOT_ANTHROPIC_API_KEY') or \
                       os.environ.get('ANTHROPIC_API_KEY') or \
                       getattr(settings, 'anthropic_api_key', None)
        
        if not anthropic_key:
            raise Exception("No Anthropic API key configured")
        
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=anthropic_key)
            
            # List all available models
            response = client.models.list()
            
            # Extract model IDs from response
            all_models = []
            if hasattr(response, 'data'):
                for model in response.data:
                    if hasattr(model, 'id'):
                        all_models.append(model.id)
                    elif hasattr(model, 'name'):
                        all_models.append(model.name)
                    elif isinstance(model, str):
                        all_models.append(model)
                    else:
                        all_models.append(str(model))
            
            if not all_models:
                raise Exception("No models returned from Anthropic API")
            
            print(f"✅ Found {len(all_models)} Anthropic models")
            return all_models
            
        except Exception as e:
            raise Exception(f"Failed to fetch Anthropic models: {e}")
    
    def _get_fallback_anthropic_models(self) -> List[str]:
        """Fallback Anthropic models when API discovery fails."""
        print("\n" + "="*60)
        print("⚠️  WARNING: Using fallback Anthropic model list!")
        print("="*60)
        print("Configure CONTEXTPILOT_ANTHROPIC_API_KEY to discover models")
        print("from the Anthropic API automatically. The fallback list may")
        print("be outdated and missing newer models.")
        print("="*60 + "\n")
        
        # Note: Update this list when new Claude versions are released
        # As of Jan 2026, Claude 4.5 models are the latest available
        return [
            # Claude 4.5 series (Latest - 2025)
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            
            # Claude 4.5 aliases (auto-update to latest snapshot)
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
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
    
    def _load_api_key_from_cache(self) -> None:
        """Load API keys from cache if not set in environment."""
        # Load OpenAI API key
        env_openai_key = os.environ.get('CONTEXTPILOT_OPENAI_API_KEY', '')
        if env_openai_key:
            self.cached_openai_key = env_openai_key
        else:
            self.cached_openai_key = None
            
        # Load Anthropic API key
        env_anthropic_key = os.environ.get('CONTEXTPILOT_ANTHROPIC_API_KEY', '')
        if env_anthropic_key:
            self.cached_anthropic_key = env_anthropic_key
        else:
            self.cached_anthropic_key = None
        
        # Try to load from cache if env vars not set
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Load OpenAI key from cache if not in env
            if not env_openai_key:
                cached_openai = cache_data.get("openai_api_key", "")
                if cached_openai:
                    self.cached_openai_key = cached_openai
                    settings.openai_api_key = cached_openai
                    print("🔑 Using OpenAI API key from cache")
            
            # Load Anthropic key from cache if not in env
            if not env_anthropic_key:
                cached_anthropic = cache_data.get("anthropic_api_key", "")
                if cached_anthropic:
                    self.cached_anthropic_key = cached_anthropic
                    settings.anthropic_api_key = cached_anthropic
                    print("🔑 Using Anthropic API key from cache")
        except Exception:
            pass
    
    def _save_cache(self, models: Dict[str, List[str]]) -> None:
        """Save models to cache."""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "models": models
        }
        
        # Store OpenAI API key
        env_openai_key = os.environ.get('CONTEXTPILOT_OPENAI_API_KEY', '')
        if env_openai_key:
            cache_data["openai_api_key"] = env_openai_key
        elif hasattr(self, 'cached_openai_key') and self.cached_openai_key:
            cache_data["openai_api_key"] = self.cached_openai_key
        
        # Store Anthropic API key
        env_anthropic_key = os.environ.get('CONTEXTPILOT_ANTHROPIC_API_KEY', '')
        if env_anthropic_key:
            cache_data["anthropic_api_key"] = env_anthropic_key
        elif hasattr(self, 'cached_anthropic_key') and self.cached_anthropic_key:
            cache_data["anthropic_api_key"] = self.cached_anthropic_key
        
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
#!/usr/bin/env python3
"""
Synchronize model lists between backend and frontend.

This script ensures valid_models.json and frontend/src/model_options.json
stay in sync. It can be run manually or as part of a build process.

Usage:
    python sync_models.py              # Sync (prefer backend as source)
    python sync_models.py --frontend   # Sync (prefer frontend as source)
    python sync_models.py --check      # Check if they're in sync without modifying
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
import argparse


def load_models(file_path: Path) -> Dict[str, Any]:
    """Load models from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def save_models(file_path: Path, models: Dict[str, Any]) -> bool:
    """Save models to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(models, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


def models_equal(models1: Dict[str, Any], models2: Dict[str, Any]) -> bool:
    """Check if two model dictionaries are equal."""
    if set(models1.keys()) != set(models2.keys()):
        return False
    
    for provider in models1:
        # Sort lists for comparison (order doesn't matter)
        list1 = sorted(models1.get(provider, []))
        list2 = sorted(models2.get(provider, []))
        
        if list1 != list2:
            return False
    
    return True


def format_models_for_sync(models: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure models dict has consistent formatting and order."""
    formatted = {}
    # Standard provider order
    for provider in ['openai', 'anthropic', 'ollama']:
        if provider in models:
            formatted[provider] = models[provider]
    return formatted


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize model lists between backend and frontend'
    )
    parser.add_argument(
        '--frontend',
        action='store_true',
        help='Use frontend as source of truth'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if files are in sync (no modifications)'
    )
    
    args = parser.parse_args()
    
    # Determine paths (script is in root of ContextPilot)
    root_dir = Path(__file__).parent  # ContextPilot root
    backend_file = root_dir / 'backend' / 'valid_models.json'
    frontend_file = root_dir / 'frontend' / 'src' / 'model_options.json'
    
    # Check files exist
    if not backend_file.exists():
        print(f"❌ Backend file not found: {backend_file}")
        return 1
    
    if not frontend_file.exists():
        print(f"❌ Frontend file not found: {frontend_file}")
        return 1
    
    # Load both files
    backend_models = load_models(backend_file)
    frontend_models = load_models(frontend_file)
    
    # Check if they're equal
    if models_equal(backend_models, frontend_models):
        print("✅ Models are already in sync!")
        return 0
    
    # If checking only, report and exit
    if args.check:
        print("⚠️ Models are out of sync:")
        print(f"  Backend:  {backend_file}")
        print(f"  Frontend: {frontend_file}")
        
        # Show differences
        for provider in set(list(backend_models.keys()) + list(frontend_models.keys())):
            backend_list = sorted(backend_models.get(provider, []))
            frontend_list = sorted(frontend_models.get(provider, []))
            
            if backend_list != frontend_list:
                print(f"\n  {provider}:")
                backend_set = set(backend_list)
                frontend_set = set(frontend_list)
                
                only_in_backend = backend_set - frontend_set
                only_in_frontend = frontend_set - backend_set
                
                if only_in_backend:
                    print(f"    Only in backend: {sorted(only_in_backend)}")
                if only_in_frontend:
                    print(f"    Only in frontend: {sorted(only_in_frontend)}")
        
        return 1
    
    # Determine source of truth
    source_file = frontend_file if args.frontend else backend_file
    target_file = backend_file if args.frontend else frontend_file
    source_models = frontend_models if args.frontend else backend_models
    
    source_name = "frontend" if args.frontend else "backend"
    target_name = "backend" if args.frontend else "frontend"
    
    # Format and save
    formatted = format_models_for_sync(source_models)
    
    if save_models(target_file, formatted):
        print(f"✅ Synchronized {target_name} with {source_name}:")
        print(f"   {source_file}")
        print(f"   → {target_file}")
        return 0
    else:
        print(f"❌ Failed to sync files")
        return 1


if __name__ == '__main__':
    sys.exit(main())

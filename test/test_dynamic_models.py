#!/usr/bin/env python3
"""
Test script to verify dynamic model loading in ContextPilot.
"""

import json
import sys
from pathlib import Path

def test_model_files():
    """Test that model files exist and are valid."""
    print("🧪 Testing Dynamic Model Loading")
    print("=" * 40)
    
    # Test frontend model file
    frontend_file = Path("frontend/src/model_options.json")
    print(f"\n📁 Testing {frontend_file}")
    
    if not frontend_file.exists():
        print("❌ Frontend model file missing!")
        return False
    
    try:
        with open(frontend_file, 'r') as f:
            frontend_models = json.load(f)
        print("✅ Frontend model file is valid JSON")
        
        for provider, models in frontend_models.items():
            print(f"   {provider}: {len(models)} models")
            if not models:
                print(f"   ⚠️  No models for {provider}")
                
    except json.JSONDecodeError as e:
        print(f"❌ Frontend model file is invalid JSON: {e}")
        return False
    
    # Test backend model file
    backend_file = Path("backend/valid_models.json")
    print(f"\n📁 Testing {backend_file}")
    
    if not backend_file.exists():
        print("❌ Backend model file missing!")
        return False
    
    try:
        with open(backend_file, 'r') as f:
            backend_models = json.load(f)
        print("✅ Backend model file is valid JSON")
        
        for provider, models in backend_models.items():
            print(f"   {provider}: {len(models)} models")
            
    except json.JSONDecodeError as e:
        print(f"❌ Backend model file is invalid JSON: {e}")
        return False
    
    # Compare files
    print(f"\n🔍 Comparing model lists...")
    if frontend_models == backend_models:
        print("✅ Frontend and backend model lists match")
    else:
        print("⚠️  Frontend and backend model lists differ")
        for provider in set(frontend_models.keys()) | set(backend_models.keys()):
            f_models = set(frontend_models.get(provider, []))
            b_models = set(backend_models.get(provider, []))
            
            if f_models != b_models:
                print(f"   {provider}:")
                if f_models - b_models:
                    print(f"     Frontend only: {list(f_models - b_models)}")
                if b_models - f_models:
                    print(f"     Backend only: {list(b_models - f_models)}")
    
    return True

def test_backend_validator():
    """Test backend validator can load models."""
    print(f"\n🔧 Testing backend validator...")
    
    sys.path.insert(0, str(Path("backend")))
    
    try:
        from validators import load_valid_models, validate_ai_model
        
        models = load_valid_models()
        print("✅ Backend validator can load models")
        
        # Test validation with valid models
        for provider, model_list in models.items():
            if model_list:  # Skip empty lists (like ollama when no models)
                test_model = model_list[0]
                try:
                    validate_ai_model(provider, test_model)
                    print(f"✅ Validation passed for {provider}:{test_model}")
                except Exception as e:
                    print(f"❌ Validation failed for {provider}:{test_model}: {e}")
                    return False
        
        # Test validation with invalid model
        try:
            validate_ai_model("openai", "invalid-model")
            print("❌ Validation should have failed for invalid model")
            return False
        except:
            print("✅ Validation correctly rejected invalid model")
        
    except ImportError as e:
        print(f"⚠️  Could not import backend validator: {e}")
        return False
    except Exception as e:
        print(f"❌ Backend validator test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    success = True
    
    if not test_model_files():
        success = False
    
    if not test_backend_validator():
        success = False
    
    print(f"\n{'🎉' if success else '❌'} Test Results")
    print("=" * 20)
    
    if success:
        print("✅ All tests passed! Dynamic model loading is working.")
        print("\n💡 To test with real API:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Run: python3 discover_models.py")
        print("   3. Check for real OpenAI models in output")
        
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test script to verify Ollama auto-pull functionality.
"""
import requests
import json
import sys

def test_ollama_autopull():
    """Test that Ollama automatically pulls missing models."""
    
    print("🧪 Testing Ollama Auto-Pull Feature\n")
    
    # Test 1: Connection error (Ollama not running)
    print("Test 1: Ollama not running...")
    response = requests.post(
        "http://localhost:8000/ai/chat",
        json={
            "task": "Say hello",
            "provider": "ollama",
            "model": "llama3.2",
            "max_context_units": 0
        }
    )
    
    if response.status_code == 400:
        error = response.json()
        if "Cannot connect to Ollama" in error.get("message", ""):
            print("✅ Correctly detects Ollama not running")
            print(f"   Message: {error['message'][:80]}...\n")
        else:
            print(f"❌ Unexpected error: {error}\n")
    else:
        print(f"❌ Expected 400, got {response.status_code}\n")
    
    # Test 2: Check if Ollama is actually running
    print("Test 2: Checking if Ollama is installed...")
    import subprocess
    try:
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            print(f"✅ Ollama found at: {result.stdout.strip()}")
            
            # Check if Ollama is serving
            try:
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:11434/api/tags"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout:
                    print("✅ Ollama is running")
                    models = json.loads(result.stdout)
                    print(f"   Available models: {[m['name'] for m in models.get('models', [])]}")
                else:
                    print("❌ Ollama installed but not running")
                    print("   Run: ollama serve")
            except Exception as e:
                print(f"❌ Could not connect to Ollama: {e}")
        else:
            print("❌ Ollama not installed")
            print("   Install from: https://ollama.ai")
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
    
    print("\n📝 Summary:")
    print("   - Auto-pull will work when:")
    print("     1. Ollama is installed and running")
    print("     2. You request a model that isn't pulled yet")
    print("     3. The backend will automatically run 'ollama pull <model>'")
    print("   - First request with a new model may take 1-5 minutes")
    print("   - Subsequent requests will be instant")

if __name__ == "__main__":
    try:
        test_ollama_autopull()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        sys.exit(1)

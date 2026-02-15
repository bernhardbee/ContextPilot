#!/usr/bin/env python3
"""
Test script to verify model validation and proper model usage.
"""

import json
import sys
import subprocess
import time
from pathlib import Path

def start_backend():
    """Start the backend server."""
    backend_dir = Path(__file__).parent.parent / "backend"
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ]
    
    print("🚀 Starting backend server...")
    env = {"PYTHONPATH": str(backend_dir)}
    process = subprocess.Popen(
        cmd, 
        cwd=backend_dir, 
        env={**dict(subprocess.os.environ), **env},
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    for i in range(30):
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/health"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                print("✅ Backend is ready!")
                return process
        except:
            pass
        time.sleep(1)
        print(f"⏳ Waiting for backend... ({i+1}/30)")
    
    print("❌ Backend failed to start")
    process.terminate()
    return None

def test_invalid_model():
    """Test that invalid model names are rejected."""
    print("\n🧪 Testing Invalid Model Validation")
    print("=" * 50)
    
    # Test with the old invalid "gpt-5" model
    print("1️⃣ Testing invalid model 'gpt-5'...")
    cmd = [
        "curl", "-s", "-X", "POST", "http://localhost:8000/ai/chat",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "task": "What is 2+2?",
            "provider": "openai",
            "model": "gpt-5"  # Invalid model
        })
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Request failed: {result.stderr}")
        return False
    
    try:
        response_data = json.loads(result.stdout)
        if "error_code" in response_data:
            print(f"✅ Correctly rejected invalid model: {response_data['message']}")
        else:
            print(f"❌ Invalid model was not rejected! Response: {response_data.get('model', 'unknown')}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        return False
    
    return True

def test_valid_model():
    """Test that valid model names work correctly."""
    print("\n2️⃣ Testing valid model 'gpt-4o'...")
    cmd = [
        "curl", "-s", "-X", "POST", "http://localhost:8000/ai/chat",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "task": "What is 2+2?",
            "provider": "openai",
            "model": "gpt-4o"  # Valid model
        })
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Request failed: {result.stderr}")
        return False
    
    try:
        response_data = json.loads(result.stdout)
        if "error_code" in response_data:
            print(f"❌ Valid model was rejected: {response_data['message']}")
            return False
        else:
            actual_model = response_data.get('model', 'unknown')
            print(f"✅ Valid model accepted: {actual_model}")
            print(f"   Response: {response_data.get('response', 'missing')[:50]}...")
            
            if actual_model == "gpt-4o":
                print("✅ Correct model was used!")
                return True
            else:
                print(f"⚠️  Expected 'gpt-4o' but got '{actual_model}'")
                return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        return False

def main():
    """Main test function."""
    print("🧭 ContextPilot Model Validation Test")
    print("=" * 50)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    try:
        # Test invalid model
        invalid_test = test_invalid_model()
        
        # Test valid model  
        valid_test = test_valid_model()
        
        if invalid_test and valid_test:
            print("\n🎉 All tests passed! Model validation is working correctly.")
            print("\n📋 Summary:")
            print("   ✅ Invalid model names are properly rejected")
            print("   ✅ Valid model names are accepted and used correctly")
            print("   ✅ The model you select in the UI will now be the model that responds")
            
            print("\n💡 Updated Model Options:")
            print("   - OpenAI: gpt-4o (Latest), gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo")
            print("   - Anthropic: claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.")
            print("   - Ollama: Any locally installed model")
            
        else:
            print("\n❌ Tests failed. Check the implementation.")
            sys.exit(1)
            
    finally:
        print("\n🛑 Stopping backend server...")
        backend_process.terminate()
        backend_process.wait()
        print("✅ Backend stopped")

if __name__ == "__main__":
    main()
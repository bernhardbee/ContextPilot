# Ollama Setup Guide for ContextPilot

## 🎯 Quick Start (Auto-Download Enabled!)

ContextPilot now **automatically downloads models** when you select them! You can skip the manual model installation and jump straight to step 3.

### Minimal Setup (Recommended)

1. **Install Ollama**: Download from https://ollama.ai
2. **Start Ollama**: Run `ollama serve` 
3. **Use ContextPilot**: Select "Ollama (Local)" provider and any model - it will auto-download!

**First request with a new model takes 1-5 minutes. Subsequent requests are instant!**

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

**macOS:**
```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.ai
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai

### 2. Pull a Model (Optional - Auto-Download Available)

**Manual Installation:**
```bash
# Recommended: Llama 3.2 (general purpose)
ollama pull llama3.2

# Other options:
ollama pull mistral      # Fast and efficient
ollama pull codellama    # Specialized for code
ollama pull phi3         # Lightweight model
ollama pull llama3.1     # Previous Llama version
```

**Automatic Download:**
You can skip this step! When you select a model in ContextPilot that isn't installed, it will automatically download it for you. Your first request will take 1-5 minutes (depending on model size), but subsequent requests will be instant.

**Note:** Manual pre-installation is faster if you know which model you want to use.

### 3. Start Ollama Server

```bash
ollama serve
```

The server will start on `http://localhost:11434` by default.

**Note:** On macOS, Ollama may start automatically as a background service after installation.

### 4. Configure ContextPilot

1. Open ContextPilot at http://localhost:3000
2. Click the ⚙️ Settings button
3. In the "API Keys" section:
   - **Ollama Base URL**: `http://localhost:11434` (default)
   - Status should show "✅ Configured"
4. In the "AI Settings" section:
   - **Default Provider**: Select "Ollama (Local)"
   - **Default Model**: Select your downloaded model (e.g., "llama3.2")
5. Click "Save Settings"

### 5. Test It!

Go back to the chat interface and ask a question. Your request will be processed entirely locally with no data sent to external services.

## Troubleshooting

### Error: "Cannot connect to Ollama server"

**Solution:**
1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   If you get a connection error, start Ollama:
   ```bash
   ollama serve
   ```

2. Verify models are installed:
   ```bash
   ollama list
   ```

### Error: "Model 'llama3.2' not found"

**Solution:**
Pull the model first:
```bash
ollama pull llama3.2
```

### Ollama on a Different Port or Host

If Ollama is running on a different port or remote machine:

1. Open Settings in ContextPilot
2. Update "Ollama Base URL" to your custom URL (e.g., `http://192.168.1.100:11434`)
3. Save settings

## Model Recommendations

| Model | Size | RAM Needed | Best For |
|-------|------|------------|----------|
| **phi3** | 2GB | 4GB | Quick responses, limited RAM |
| **llama3.2** | 2-4GB | 8GB | General purpose (Recommended) |
| **mistral** | 4GB | 8GB | Fast and efficient |
| **llama3.1** | 4GB | 8GB | Previous stable version |
| **codellama** | 7GB | 16GB | Code generation and analysis |

## Benefits of Local Models

✅ **Privacy**: Your data never leaves your machine  
✅ **Cost**: No API fees  
✅ **Speed**: No network latency  
✅ **Offline**: Works without internet  
✅ **Unlimited**: No rate limits or quotas  

## Advanced Usage

### Custom Ollama Configuration

Edit `backend/.env`:
```bash
CONTEXTPILOT_OLLAMA_BASE_URL=http://localhost:11434
CONTEXTPILOT_DEFAULT_AI_PROVIDER=ollama
CONTEXTPILOT_DEFAULT_AI_MODEL=llama3.2
```

### Running Multiple Models

You can switch between models in the chat interface without reconfiguring. Simply select a different model from the dropdown.

### Updating Models

```bash
# Check for updates
ollama list

# Pull latest version
ollama pull llama3.2
```

## Resources

- Official Ollama Documentation: https://github.com/ollama/ollama
- Model Library: https://ollama.ai/library
- ContextPilot AI Integration Guide: `backend/docs/AI_INTEGRATION.md`

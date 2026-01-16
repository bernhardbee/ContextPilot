# AI Integration Guide

ContextPilot integrates with multiple AI providers to generate responses using your managed context.

## Supported Providers

### OpenAI
- **Models**: Dynamically discovered from OpenAI API (GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-4, GPT-3.5-turbo, etc.)
- **API**: OpenAI Chat Completions API
- **Features**: Function calling, streaming, vision (GPT-4V)
- **Discovery**: Real-time model list via API when key is configured

### Anthropic
- **Models**: Claude 3.5 Sonnet (latest), Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **API**: Anthropic Messages API
- **Features**: Extended context windows, thinking tokens
- **Discovery**: Curated list of current models (updated regularly)

### Ollama (Local Models)
- **Models**: Automatically detected from local installation (llama3.2, mistral, codellama, phi3, etc.)
- **API**: OpenAI-compatible REST API
- **Features**: Local execution, privacy, no API costs, offline support
- **Requirements**: Ollama installed locally (https://ollama.ai)
- **Discovery**: Live detection of installed models via API and CLI

## Quick Start

### 1. Get API Keys (or Install Ollama)

**OpenAI**:
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

**Anthropic**:
1. Visit https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

**Ollama (Local)**:
1. Download and install from https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama server: `ollama serve` (runs on http://localhost:11434)
4. No API key required!

### 2. Configure API Keys / Ollama

**Option A: Settings UI (Easiest)**

1. Open the web interface at http://localhost:3000
2. Click the ⚙️ settings button in the header
3. Enter your API key(s) OR configure Ollama:
   - **OpenAI**: Paste your `sk-` key
   - **Anthropic**: Paste your `sk-ant-` key
   - **Ollama Base URL**: http://localhost:11434 (default)
4. Configure AI parameters:
   - Provider: `openai`, `anthropic`, or `ollama`
   - Model: Select from dropdown based on provider
   - Temperature: 0-2 (default 1.0)
   - Max Tokens: 1-16000 (default 4000)
     - Increase for image-heavy responses (8000+)
     - Prevents truncation of long responses
5. Click "Save Settings"

Settings apply immediately - no restart required!

**Option B: Environment File**

Add to your `.env` file:

```bash
# OpenAI Configuration
CONTEXTPILOT_OPENAI_API_KEY=sk-your-openai-api-key
CONTEXTPILOT_DEFAULT_AI_PROVIDER=openai
CONTEXTPILOT_DEFAULT_AI_MODEL=gpt-4-turbo-preview

# Or Anthropic Configuration
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
CONTEXTPILOT_DEFAULT_AI_PROVIDER=anthropic
CONTEXTPILOT_DEFAULT_AI_MODEL=claude-3-opus-20240229

# Or Ollama Configuration (Local)
CONTEXTPILOT_OLLAMA_BASE_URL=http://localhost:11434
CONTEXTPILOT_DEFAULT_AI_PROVIDER=ollama
CONTEXTPILOT_DEFAULT_AI_MODEL=llama3.2

# AI Parameters
CONTEXTPILOT_AI_MAX_TOKENS=4000  # Supports up to 16000
CONTEXTPILOT_AI_TEMPERATURE=1.0
```

Note: Restart backend after changing .env file.

### 3. Test the Integration

```bash
curl -X POST http://localhost:8002/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Explain the main purpose of this codebase",
    "max_context_units": 5
  }'
```

## API Endpoints

### POST /ai/chat

Generate an AI response using relevant context.

**Request Body**:
```json
{
  "task": "Your question or task",
  "max_context_units": 5,
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "temperature": 0.7,
  "max_tokens": 2000,
  "use_compact": false
}
```

**Parameters**:
- `task` (required): The question or task for the AI
- `max_context_units` (optional): Maximum context items to include (default: 10)
- `provider` (optional): "openai", "anthropic", or "ollama" (uses default if not specified)
- `model` (optional): Model name (uses default if not specified)
  - OpenAI: `gpt-5`, `gpt-4o`, `gpt-4-turbo`, etc.
  - Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, etc.
  - Ollama: `llama3.2`, `mistral`, `codellama`, `phi3`, etc.
- `temperature` (optional): 0.0-1.0 (default: 0.7)
- `max_tokens` (optional): Maximum response length (default: 2000)
- `use_compact` (optional): Use compact prompt format (default: false)

**Response**:
```json
{
  "conversation_id": "conv_abc123",
  "task": "Your question or task",
  "response": "AI generated response...",
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "context_ids": ["ctx1", "ctx2", "ctx3"],
  "prompt_used": "Full prompt sent to AI...",
  "timestamp": "2024-01-15T10:30:00"
}
```

### GET /ai/conversations

List all conversation history.

**Response**:
```json
[
  {
    "id": "conv_abc123",
    "task": "Explain the main purpose",
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "created_at": "2024-01-15T10:30:00",
    "message_count": 2
  }
]
```

### GET /ai/conversations/{conversation_id}

Get a specific conversation with full message history.

**Response**:
```json
{
  "id": "conv_abc123",
  "task": "Explain the main purpose",
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "created_at": "2024-01-15T10:30:00",
  "messages": [
    {
      "role": "user",
      "content": "Explain the main purpose of this codebase",
      "timestamp": "2024-01-15T10:30:00",
      "tokens": null
    },
    {
      "role": "assistant",
      "content": "This codebase is designed to...",
      "timestamp": "2024-01-15T10:30:05",
      "tokens": 150,
      "finish_reason": "stop"
    }
  ]
}
```

### GET /settings

Get current AI configuration settings.

**Response**:
```json
{
  "openai_api_key_set": true,
  "anthropic_api_key_set": false,
  "ollama_configured": true,
  "ollama_base_url": "http://localhost:11434",
  "ai_provider": "ollama",
  "ai_model": "llama3.2",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Note**: API keys are never exposed - only boolean flags indicating if they're configured.

### POST /settings

Update AI configuration settings.

**Request Body**:
```json
{
  "openai_api_key": "sk-your-key-here",
  "anthropic_api_key": "sk-ant-your-key-here",
  "ollama_base_url": "http://localhost:11434",
  "ai_provider": "ollama",
  "ai_model": "llama3.2",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**All fields are optional** - only provide the settings you want to update.

**Validation**:
- `temperature`: Must be between 0 and 2
- `max_tokens`: Must be between 1 and 4000
- `ai_provider`: Must be "openai", "anthropic", or "ollama"

**Response**: Same as GET /settings

**Note**: Settings apply immediately - AI service is automatically reinitialized with new credentials.

## Dynamic Model Discovery

ContextPilot features an advanced model discovery system that automatically detects available models from each provider, ensuring you always have access to current, working models.

### How It Works

**OpenAI**: When an API key is configured, the system queries the OpenAI API to fetch available chat models in real-time.
- Models like `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`
- Automatically filters for chat-compatible models
- Sorts by capability and recency

**Anthropic**: Maintains a curated list of current Anthropic models since they don't provide a public discovery API.
- Regularly updated with latest Claude models
- Includes Claude 3.5 Sonnet, Claude 3 Opus, etc.

**Ollama**: Automatically detects locally installed models via API or CLI.
- Queries `http://localhost:11434/api/tags` for available models
- Falls back to `ollama list` command if API unavailable
- Shows only models you've actually downloaded

### Model Cache & Performance

- **24-Hour Caching**: Model lists are cached for optimal performance
- **Automatic Refresh**: Backend refreshes models on startup if cache is stale
- **Manual Refresh**: Use discovery scripts for immediate updates
- **Fallback Safety**: Uses known working models if discovery fails

### Discovery Commands

```bash
# Discover all available models
python3 discover_models.py

# Force refresh (ignore cache)
python3 refresh_models.py --force

# Check current model status
python3 demo_dynamic_models.py

# Test the discovery system
python3 test_dynamic_models.py
```

### Benefits

✅ **Always Current**: No more invalid model names (like "gpt-5")
✅ **Local Detection**: Automatically finds Ollama models
✅ **Performance Optimized**: Smart caching minimizes API calls
✅ **Robust Fallbacks**: Works even when APIs are unavailable
✅ **Zero Maintenance**: Updates itself automatically

## Model Selection Guide

### OpenAI Models

| Model | Best For | Context Window | Cost/1M tokens |
|-------|----------|----------------|----------------|
| gpt-4o | Latest, most capable | 128K | $5 / $15 |
| gpt-4o-mini | Fast, cost-effective | 128K | $0.15 / $0.60 |
| gpt-4-turbo | Complex tasks, accuracy | 128K | $10 / $30 |
| gpt-4 | High quality responses | 8K | $30 / $60 |
| gpt-3.5-turbo | Fast, economical | 16K | $0.50 / $1.50 |

*Note: Exact models available depend on your API access level and are auto-discovered*

### Anthropic Models

| Model | Best For | Context Window | Cost/1M tokens |
|-------|----------|----------------|----------------|
| claude-3-5-sonnet-20241022 | Latest, most capable | 200K | $3 / $15 |
| claude-3-5-sonnet-20240620 | Previous Sonnet version | 200K | $3 / $15 |
| claude-3-opus-20240229 | Highest capability | 200K | $15 / $75 |
| claude-3-sonnet-20240229 | Balanced performance | 200K | $3 / $15 |
| claude-3-haiku-20240307 | Fast, cost-effective | 200K | $0.25 / $1.25 |

### Ollama Models (Local)

| Model | Best For | Size | Requirements |
|-------|----------|------|--------------|
| llama3.2 | General purpose, latest | 2-4GB | 8GB RAM |
| llama3.1 | General purpose | 2-4GB | 8GB RAM |
| mistral | Fast, efficient | 4GB | 8GB RAM |
| codellama | Code generation | 4-7GB | 16GB RAM |
| phi3 | Lightweight, fast | 2GB | 4GB RAM |

**Ollama Benefits**:
- ✅ **Free**: No API costs
- ✅ **Private**: Data never leaves your machine
- ✅ **Offline**: Works without internet
- ✅ **Fast**: No network latency
- ✅ **Flexible**: Many models available (https://ollama.ai/library)

**To use Ollama**:
1. Install Ollama: https://ollama.ai
2. Start server: `ollama serve`
3. Configure ContextPilot to use `ollama` provider
4. Select a model - ContextPilot will automatically download it if needed

**Auto-Download Feature:**
You don't need to manually pull models! When you select a model that isn't installed yet (like `llama3.2`), ContextPilot will automatically run `ollama pull` for you. The first request will take 1-5 minutes depending on the model size, but subsequent requests will be instant.

### Choosing a Model

**Use GPT-4 Turbo or Claude Opus when**:
- Accuracy is critical
- Complex reasoning required
- Large context needed
- Budget allows

**Use GPT-3.5 Turbo or Claude Haiku when**:
- Fast responses needed
- Simple queries
- High request volume
- Cost optimization important

**Use Claude Sonnet for**:
- Balanced price/performance
- Extended context requirements
- Conversational applications

**Use Ollama (Local Models) when**:
- Privacy is a priority
- No budget for API costs
- Offline functionality needed
- Lower latency desired
- Experimenting with different models

## Context Integration

The AI integration automatically:

1. **Retrieves relevant context** using the relevance engine
2. **Ranks and selects** top N context units
3. **Composes prompt** with context and task
4. **Calls AI provider** with composed prompt
5. **Persists conversation** in database
6. **Returns response** with metadata

### Context Ranking

Context is ranked by:
- Keyword match frequency
- Embeddings similarity (if available)
- Recency (recent > old)
- Source type priority

### Prompt Composition

Two modes available:

**Standard Format** (default):
```
You are an AI assistant helping with code understanding.

Context:
[File: src/main.py]
def main():
    ...

[File: src/utils.py]
...

Task: Explain the main purpose of this codebase
```

**Compact Format** (`use_compact: true`):
```
Context: src/main.py: def main()..., src/utils.py: ...
Task: Explain the main purpose of this codebase
```

Use compact format when:
- Context is large and model has limited window
- Cost optimization needed
- Simple queries

## Best Practices

### 1. API Key Management
```bash
# Use environment variables
export CONTEXTPILOT_OPENAI_API_KEY=sk-...

# Or .env file (add to .gitignore)
echo "CONTEXTPILOT_OPENAI_API_KEY=sk-..." >> .env
echo ".env" >> .gitignore
```

### 2. Error Handling
```python
try:
    response = requests.post("http://localhost:8002/ai/chat", json={
        "task": "Explain this code"
    })
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 500:
        print("API key not configured or invalid")
    else:
        print(f"Error: {e}")
```

### 3. Cost Optimization

**Track token usage**:
```python
# Response includes token count
tokens_used = result.get("tokens", 0)
estimated_cost = tokens_used * 0.00003  # $0.03 per 1K tokens for GPT-4
```

**Use cheaper models for simple tasks**:
```json
{
  "task": "What files are in this project?",
  "model": "gpt-3.5-turbo",
  "max_tokens": 500
}
```

**Limit context units**:
```json
{
  "task": "Explain main.py",
  "max_context_units": 3
}
```

### 4. Temperature Tuning

- **0.0-0.3**: Deterministic, focused, factual
- **0.4-0.7**: Balanced creativity and accuracy
- **0.8-1.0**: Creative, varied responses

```json
{
  "task": "Write unit tests",
  "temperature": 0.2
}
```

### 5. Conversation Continuity

Conversations are automatically persisted:

```bash
# First message
curl -X POST http://localhost:8002/ai/chat \
  -d '{"task": "Explain main.py"}'

# Get conversation ID from response
CONV_ID=conv_abc123

# View conversation history
curl http://localhost:8002/ai/conversations/$CONV_ID
```

## Troubleshooting

### "API key not configured"

**Solution**: Set the API key in `.env`:
```bash
CONTEXTPILOT_OPENAI_API_KEY=sk-your-key
# or
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-your-key
```

### "Rate limit exceeded"

**Solutions**:
1. Wait and retry (exponential backoff)
2. Upgrade API plan for higher limits
3. Use cheaper/faster model
4. Batch requests

### "Context length exceeded"

**Solutions**:
1. Reduce `max_context_units`
2. Use compact prompt format
3. Use model with larger context window
4. Split task into smaller queries

### "Invalid model"

**Solution**: Check model name:
```bash
# OpenAI
gpt-4-turbo-preview
gpt-4
gpt-3.5-turbo

# Anthropic
claude-3-opus-20240229
claude-3-sonnet-20240229
claude-3-haiku-20240307
```

### Poor response quality

**Solutions**:
1. Improve context relevance (add better context)
2. Make task more specific
3. Increase `max_context_units`
4. Use more capable model
5. Adjust temperature (lower = more focused)

## Security Considerations

1. **Never commit API keys**: Use `.gitignore` for `.env`
2. **Rotate keys regularly**: Especially if exposed
3. **Monitor usage**: Set up billing alerts
4. **Use environment variables**: Not hardcoded keys
5. **Restrict API key permissions**: Use least privilege
6. **Audit access logs**: Review API usage patterns

## Rate Limits

### OpenAI (as of 2024)
- **GPT-4**: 10K TPM, 500 RPM (free tier)
- **GPT-3.5**: 60K TPM, 3.5K RPM (free tier)
- Upgrade for higher limits

### Anthropic (as of 2024)
- **Claude**: Varies by plan
- Contact sales for production limits

## Integration Examples

### Python Client
```python
import requests

def ask_ai(task: str, max_context: int = 5):
    response = requests.post(
        "http://localhost:8002/ai/chat",
        json={
            "task": task,
            "max_context_units": max_context,
            "provider": "openai",
            "model": "gpt-4-turbo-preview"
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
result = ask_ai("What does the main function do?")
print(result["response"])
```

### JavaScript Client
```javascript
async function askAI(task, maxContext = 5) {
  const response = await fetch('http://localhost:8002/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task,
      max_context_units: maxContext,
      provider: 'openai',
      model: 'gpt-4-turbo-preview'
    })
  });
  
  if (!response.ok) throw new Error('AI request failed');
  return await response.json();
}

// Usage
const result = await askAI('What does the main function do?');
console.log(result.response);
```

## Future Enhancements

Planned features:
- Streaming responses
- Multi-turn conversations
- Function calling support
- Vision model integration (GPT-4V)
- Custom system prompts
- Response caching
- Cost tracking and limits
- A/B testing different models

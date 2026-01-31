# Dynamic Model Discovery for ContextPilot

## Overview

ContextPilot now features a dynamic model discovery system that automatically detects available AI models from each provider, replacing hardcoded model lists. This ensures the application always shows current, working models.

## How It Works

### 1. Model Discovery Process

The system discovers models from three providers:

- **OpenAI**: Fetches available chat models via API (requires API key)
- **Anthropic**: Fetches available models via `client.models.list()` API (requires API key)
- **Ollama**: Detects locally installed models via API or CLI

### 2. Files Created

- `discover_models.py` - Main discovery script
- `refresh_models.py` - Startup integration and cache management  
- `update_models.sh` - Convenient shell script for manual updates
- `test_dynamic_models.py` - Test script to validate the system
- `frontend/src/model_options.json` - Frontend model configuration
- `backend/valid_models.json` - Backend validation configuration
- `available_models_cache.json` - Cached discovery results (auto-generated)

### 3. Integration Points

- **Frontend**: Dynamically loads model options from JSON file
- **Backend**: Updates model validation to use JSON file  
- **Startup**: Optionally refreshes models when backend starts
- **Manual**: Scripts for on-demand model discovery

## Usage

### Automatic Discovery

Models are automatically discovered when:
- Backend starts up (if cache is stale)
- Cache is older than 24 hours

### Manual Discovery

Run model discovery manually:

```bash
# Full discovery (recommended)
python3 discover_models.py

# Or use the convenience script
./update_models.sh

# Force refresh regardless of cache age
python3 refresh_models.py --force

# Set custom cache age
python3 refresh_models.py --max-age 12  # 12 hours
```

### Testing the System

Validate everything is working:

```bash
python3 test_dynamic_models.py
```

## Configuration

### OpenAI API Access

For real-time OpenAI model discovery, set your API key:

```bash
export CONTEXTPILOT_OPENAI_API_KEY="your-key-here"
```

Without an API key, the system uses fallback models.

### Anthropic API Access

For real-time Anthropic model discovery, set your API key:

```bash
export CONTEXTPILOT_ANTHROPIC_API_KEY="sk-ant-..."
```

Or configure it in `backend/.env`:
```bash
CONTEXTPILOT_ANTHROPIC_API_KEY=sk-ant-...
```

Without an API key, the system uses fallback models (Claude 4.5 series).

### Ollama Detection

The system automatically detects Ollama models if:
- Ollama is running locally (default: http://localhost:11434)
- Models are installed (`ollama list` shows models)

### Cache Settings

Model lists are cached for 24 hours by default. Configure this in:
- `refresh_models.py` - Change `max_age_hours` parameter
- Backend startup - Modify the `max_age_hours` in `main.py`

## Benefits

1. **Always Current**: Shows only working, available models
2. **Automatic Updates**: Refreshes model lists automatically
3. **Local Model Support**: Detects locally installed Ollama models
4. **Robust Fallbacks**: Works even when APIs are unavailable
5. **Performance**: Caches results to minimize API calls
6. **Easy Maintenance**: No more manual model list updates

## Scheduled Updates

For production deployments, set up automatic updates:

```bash
# Add to crontab (runs daily at 6 AM)
crontab -e

# Add this line:
0 6 * * * /path/to/ContextPilot/update_models.sh
```

## Troubleshooting

### No Models Showing

1. Check if JSON files exist and contain data:
   ```bash
   cat frontend/src/model_options.json
   cat backend/valid_models.json
   ```

2. Run discovery manually:
   ```bash
   python3 discover_models.py
   ```

3. Check for errors in the output

### OpenAI Models Not Loading

1. Verify API key is set:
   ```bash
   echo $CONTEXTPILOT_OPENAI_API_KEY
   ```

2. Test API access:
   ```bash
   curl -H "Authorization: Bearer $CONTEXTPILOT_OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

### Anthropic Models Not Loading

1. Verify API key is set:
   ```bash
   echo $CONTEXTPILOT_ANTHROPIC_API_KEY
   ```

2. Test API access:
   ```bash
   python3 -c "from anthropic import Anthropic; import os; client = Anthropic(api_key=os.getenv('CONTEXTPILOT_ANTHROPIC_API_KEY')); print(client.models.list())"
   ```

3. Check if API key is in cache:
   ```bash
   python3 -c "import json; print('Key cached:', bool(json.load(open('available_models_cache.json')).get('anthropic_api_key')))"
   ```

### Ollama Models Not Detected

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Verify models are installed:
   ```bash
   ollama list
   ```

### Cache Issues

Clear the cache to force fresh discovery:
```bash
rm available_models_cache.json
python3 discover_models.py
```

## Development Notes

### Adding New Providers

To add support for a new AI provider:

1. Update `discover_models.py`:
   - Add new provider to the `models` dictionary
   - Implement discovery method (e.g., `_discover_newprovider_models()`)

2. Update frontend model display names in `App.tsx`

3. Update backend validation in `validators.py` if needed

### Customizing Model Names

The frontend shows friendly names for models. Customize these in `App.tsx` in the model option mapping logic.

### API Rate Limits

The system respects API rate limits by:
- Caching results for 24 hours
- Using fallback models when APIs fail
- Only making API calls when necessary

## Security Considerations

- API keys are loaded from environment variables or database
- No sensitive information is stored in model cache files
- All API requests use HTTPS
- Model validation prevents injection of invalid model names

## Migration from Hardcoded Models

The system automatically handles migration:
1. Old hardcoded models are replaced with dynamic loading
2. Fallback models ensure functionality if discovery fails
3. Cache provides performance equivalent to hardcoded lists
4. No user configuration changes needed

This system ensures ContextPilot always shows the most current and available AI models without manual maintenance.
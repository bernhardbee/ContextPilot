## Model Synchronization Guide

### Overview

ContextPilot maintains a **single source of truth** for available models to keep the backend and frontend in sync. This prevents discrepancies between what models are shown in the UI and what the backend API accepts.

### Architecture

**Single Source of Truth**: `backend/valid_models.json`

This JSON file defines all available models for each provider:
- OpenAI (gpt-5.2, gpt-5, gpt-4o, etc.)
- Anthropic (claude-opus-4-5, claude-sonnet-4-5, etc.)
- Ollama (llama3.2:latest, etc.)

#### Files and Their Roles

| File | Purpose | Updated By |
|------|---------|-----------|
| `backend/valid_models.json` | **Source of truth** - Central configuration | Manual edit |
| `frontend/src/model_options.json` | Copy for frontend UI | Sync script |
| `backend/providers/{openai,anthropic}_provider.py` | MODEL_INFO dictionaries | Dynamic loader |
| `backend/main.py` | `/providers` endpoint | Reads from dynamic loader |

### How It Works

#### Backend
1. **model_loader.py** provides utility functions
2. **load_models_from_json()** reads from `valid_models.json`
3. **build_model_info()** generates MODEL_INFO dictionaries with context windows, descriptions, etc.
4. **OpenAIProvider.MODEL_INFO** and **AnthropicProvider.MODEL_INFO** are dynamically loaded on startup
5. The `/providers` API endpoint returns available_models from MODEL_INFO

**Benefit**: When you update `valid_models.json`, the backend automatically picks up changes on the next restart. No code changes needed.

#### Frontend
1. Imports `model_options.json` for UI dropdowns
2. When settings modal opens, fetches available models from backend `/providers` endpoint
3. Both sources show the same models

**Benefit**: Settings modal always shows what the backend supports.

### Maintaining Models

#### When to Update Models

Update `backend/valid_models.json` when:
- New models are released (e.g., gpt-6, claude-opus-5)
- Old models are deprecated or sunset
- You want to change available options in the UI

#### How to Update

**Option 1: Manual Edit**
1. Edit `backend/valid_models.json`
2. Run sync script: `python sync_models.py`
3. Restart backend application

Example:
```json
{
  "openai": [
    "gpt-5.2",     // Add new model here
    "gpt-5",
    ...
  ],
  "anthropic": [...],
  "ollama": [...]
}
```

**Option 2: Git Workflow**
```bash
# 1. Update backend/valid_models.json
# 2. Check sync status
python sync_models.py --check

# 3. Sync frontend with backend
python sync_models.py

# 4. Commit both files
git add backend/valid_models.json frontend/src/model_options.json
git commit -m "Update available models"
```

### Sync Script

#### Usage

```bash
# Check if files are in sync
python sync_models.py --check

# Sync frontend with backend (default, prefer backend)
python sync_models.py

# Sync backend with frontend
python sync_models.py --frontend
```

#### Exit Codes
- `0`: Models are in sync (or successfully synced)
- `1`: Models are out of sync or error occurred

#### Options
- `--check`: Report differences without modifying files
- `--frontend`: Use frontend as source of truth (overwrite backend)
- (default): Use backend as source (overwrite frontend)

### Automatic Fallback

If `valid_models.json` is missing or unreadable:
1. Backend providers fall back to hardcoded MODEL_INFO
2. Frontend continues with its own `model_options.json`
3. Application still works, but changes won't sync

This ensures the app never breaks if the JSON file is missing.

### CI/CD Integration

To ensure models stay in sync in your build pipeline:

```yaml
# Example GitHub Actions step
- name: Sync models
  run: |
    python sync_models.py --check
    if [ $? -ne 0 ]; then
      echo "❌ Models out of sync"
      exit 1
    fi
```

Or auto-sync as part of build:
```yaml
- name: Sync models
  run: python sync_models.py
```

### Troubleshooting

#### "Models out of sync" on commit

Run: `python sync_models.py`

Then commit both modified files.

#### Settings modal shows old models

Restart the backend application to reload `valid_models.json`:
```bash
# If using the start task
Ctrl+C to stop
# Run start task again
```

#### New model not appearing in UI

1. Add model to `backend/valid_models.json`
2. Run `python sync_models.py`
3. Verify both files were updated: `git status`
4. Restart backend application

### Implementation Details

**Dynamic Loader Functions** (backend/model_loader.py):

```python
load_models_from_json()        # Load from valid_models.json
build_model_info()             # Generate MODEL_INFO with metadata
format_model_name()            # Format model names for display
get_context_window()           # Get context window for model
supports_temperature()         # Check if model supports temp
get_model_description()        # Get model description
```

**Provider Integration**:
- `OpenAIProvider._load_openai_models()` - Dynamic loader for GPT models
- `AnthropicProvider._load_anthropic_models()` - Dynamic loader for Claude models

**Validators**:
- `backend/validators.py` also reads from `valid_models.json`
- Ensures API rejects unsupported models with clear error messages

### Future Enhancements

Possible improvements:
- [ ] Auto-fetch models from OpenAI/Anthropic APIs on startup
- [ ] Model capabilities database (vision, function calling, etc.)
- [ ] Pricing and cost estimation per model
- [ ] Model release date and deprecation warnings
- [ ] Web UI for managing models without editing JSON

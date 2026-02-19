# ContextPilot Backend

FastAPI backend for ContextPilot - a multi-model AI chat interface with context management.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Testing

Run all tests:
```bash
python -m pytest  # All tests
python -m pytest --ignore=test_integration.py  # Unit-focused subset
```

Run specific test suites:
```bash
pytest test_validators.py -v
pytest test_security.py -v
pytest test_api_security.py -v
pytest test_ai_service.py -v
pytest test_settings.py -v
```

## Database Management

Backup and restore database:
```bash
./backup_db.sh   # Create timestamped backup
./restore_db.sh  # Restore from backup
```

## Features

- **Context Management**: CRUD operations for context units
- **Semantic Search**: Relevance ranking using embeddings
- **Prompt Generation**: Full and compact prompt composition
- **AI Chat**: OpenAI and Anthropic integration with conversation history
- **Image Support**: Markdown image rendering in chat responses
- **Database Storage**: SQLite/PostgreSQL with Alembic migrations
- **Import/Export**: JSON and CSV import/export functionality
- **Settings Management**: API key and AI configuration (max 16K tokens)
- **Dynamic Model Loading**: Single source of truth for model lists (valid_models.json)
- **Provider-Specific Settings**: Temperature, top_p, max_tokens overrides per provider
- **Model Synchronization**: Automatic frontend/backend sync with sync_models.py
- **Security**: API key authentication, input validation, CORS, rate limiting
- **Testing**: 207 collected backend tests (`206 passed, 1 skipped` in local run)
- **Attribution Integrity**: `/ai/chat` returns authoritative executed provider/model metadata
- **Provider Switch Safety**: Conversation provider/model metadata is updated on each generated response
- **Ollama Auto-Pull Test**: Environment-aware integration test supports both
    - expected connection-error behavior when Ollama is offline, and
    - successful responses when Ollama is already running locally

## Model System

### Dynamic Model Loading

All models are loaded dynamically from a single source of truth:

```
backend/valid_models.json (Single Source)
    ↓
backend/model_loader.py (Loading Utilities)
    ↓
backend/providers/* (OpenAI, Anthropic, Ollama)
    ↓
Frontend (via /providers endpoint)
```

**Files:**
- `model_loader.py`: Utilities for loading models and building metadata
- `valid_models.json`: Master model catalog (safe to commit)
- `providers/openai_provider.py`: Dynamic OpenAI model loading
- `providers/anthropic_provider.py`: Dynamic Anthropic model loading
- `providers/ollama_provider.py`: Ollama local model support

**Key Features:**
- Models update automatically when valid_models.json changes
- Fallback to hardcoded models if JSON loading fails
- Provider-specific settings (temperature, top_p, max_tokens, etc.)
- Model metadata (context windows, naming conventions, feature support)

### Synchronization

Keep frontend and backend in sync:

```bash
# From repository root
python bin/sync_models.py              # Sync frontend ← backend
python bin/sync_models.py --check      # Validate synchronization
python bin/sync_models.py --frontend   # Sync backend ← frontend
```

See [MODEL_SYNCHRONIZATION.md](../docs/MODEL_SYNCHRONIZATION.md) for details.

### Provider Integration

Each provider implements dynamic model loading:

```python
# OpenAI Provider
from providers.openai_provider import OpenAIProvider
provider = OpenAIProvider(api_key="sk-...")
models = provider.MODEL_INFO  # Dynamically loaded from valid_models.json
```

See [PROVIDER_INTEGRATION.md](../docs/PROVIDER_INTEGRATION.md) for configuration details.

## Project Structure

```
backend/
├── main.py                  # FastAPI application entry point
├── model_loader.py          # Dynamic model loading utilities
├── models.py                # Pydantic data models
├── db_models.py             # SQLAlchemy database models
├── storage.py               # In-memory storage implementation
├── db_storage.py            # Database storage implementation
├── storage_interface.py     # Storage interface abstraction
├── relevance.py             # Relevance ranking engine
├── composer.py              # Prompt composition logic
├── ai_service.py            # OpenAI/Anthropic integration
├── config.py                # Configuration management
├── logger.py                # Logging system
├── validators.py            # Input validation
├── security.py              # Authentication & security
├── exceptions.py            # Custom exception classes
├── error_models.py          # Error response models
├── dependencies.py          # FastAPI dependency injection
├── database.py              # Database session management
├── embedding_cache.py       # Embedding caching layer
├── response_cache.py        # Response caching system
├── request_tracking.py      # Request tracking & analytics
├── example_data.py          # Example data loader
├── init_db.py               # Database initialization
├── migrate.py               # Database migration utilities
├── migrate_to_db.py         # Migration from in-memory to DB
├── valid_models.json        # Model catalog (single source of truth)
├── providers/               # LLM provider implementations
│   ├── openai_provider.py   # OpenAI with dynamic model loading
│   ├── anthropic_provider.py # Anthropic with dynamic model loading
│   └── ollama_provider.py   # Ollama local provider
├── alembic/                 # Database migration scripts
├── alembic.ini              # Alembic configuration
├── docs/                    # API documentation
├── test_*.py                # Test suites (204 tests)
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project configuration
└── .env.example             # Environment variables template
```

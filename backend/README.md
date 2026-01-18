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
python -m pytest --ignore=test_integration.py  # Unit tests only (135 passing)
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
- **Security**: API key authentication, input validation, CORS, rate limiting
- **Testing**: 135+ comprehensive unit tests across multiple suites

## Project Structure

```
backend/
├── main.py                  # FastAPI application entry point
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
├── alembic/                 # Database migration scripts
├── alembic.ini              # Alembic configuration
├── docs/                    # API documentation
├── test_*.py                # Test suites (107 tests)
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project configuration
└── .env.example             # Environment variables template
```

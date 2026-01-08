# ContextPilot Backend

FastAPI backend for ContextPilot - an AI-powered personal context engine.

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
pytest -v
```

Run specific test suites:
```bash
pytest test_validators.py -v
pytest test_security.py -v
pytest test_api_security.py -v
```

## Features

- **Context Management**: CRUD operations for context units
- **Semantic Search**: Relevance ranking using embeddings
- **Prompt Generation**: Full and compact prompt composition
- **Security**: API key authentication, input validation, CORS
- **Testing**: 82 comprehensive tests

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── models.py            # Data models
├── storage.py           # In-memory storage
├── relevance.py         # Relevance engine
├── composer.py          # Prompt composer
├── config.py            # Configuration management
├── logger.py            # Logging system
├── validators.py        # Input validation
├── security.py          # Authentication
├── example_data.py      # Example data loader
├── test_*.py            # Test suites (82 tests)
└── requirements.txt     # Dependencies
```
├── storage.py           # In-memory storage
├── relevance.py         # Relevance engine
├── composer.py          # Prompt composer
├── config.py            # Configuration management
├── logger.py            # Logging system
├── validators.py        # Input validation
├── security.py          # Authentication
├── prompt_logger.py     # Prompt logging & audit
├── example_data.py      # Example data loader
├── test_*.py            # Test suites (107 tests)
└── requirements.txt     # Dependencies
```

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

Run the test script:
```bash
python test_api.py
```

## Project Structure

```
backend/
├── main.py           # FastAPI application
├── models.py         # Data models
├── storage.py        # In-memory storage
├── relevance.py      # Relevance engine
├── composer.py       # Prompt composer
├── example_data.py   # Example data loader
└── test_api.py       # Test script
```

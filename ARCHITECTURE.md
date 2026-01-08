# ContextPilot - System Architecture

## Overview

ContextPilot is an AI-powered personal context engine with three main layers:

1. **Frontend Layer** - React UI for user interaction
2. **Backend Layer** - FastAPI server with business logic
3. **Storage Layer** - Database (PostgreSQL/SQLite) or in-memory store with vector embeddings

## Recent Architectural Improvements

### 1. Storage Interface Abstraction
- **Problem**: Storage implementations (in-memory vs database) had no formal contract
- **Solution**: Introduced `ContextStoreInterface` abstract base class
- **Benefits**:
  - Type safety and IDE support
  - Swappable implementations
  - Easier testing and mocking
  - Clear API contract

### 2. Database Session Management
- **Problem**: Manual commit/rollback, potential session leaks
- **Solution**: Enhanced context manager with automatic commit and guaranteed cleanup
- **Implementation**:
  - Auto-commit on success
  - Auto-rollback on exceptions
  - Guaranteed session cleanup
  - Improved error logging
- **Impact**: Eliminates session leaks and data consistency issues

### 3. API Rate Limiting
- **Implementation**: slowapi with per-IP rate limiting
- **Limits**:
  - Context operations: 100/minute
  - Prompt generation: 50/minute
  - AI chat (most expensive): 10/minute
- **Benefits**: Prevents abuse, protects API costs

### 4. Standardized Error Handling
- **Custom Exceptions**: All errors inherit from `ContextPilotException`
- **Error Response Format**:
  ```json
  {
    "error_code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {}
  }
  ```
- **Global Handlers**: Consistent error format across all endpoints
- **Benefits**: Better API UX, easier debugging

### 5. Synchronous AI Service
- **Decision**: Removed false async patterns from AI service
- **Rationale**: API calls to OpenAI/Anthropic are blocking I/O
- **Implementation**: Changed from `async def` to `def` for clarity
- **Documentation**: Added notes explaining synchronous design choice

## System Components

### 1. Frontend (React + TypeScript)

```
┌─────────────────────────────────────┐
│          React Application          │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │      App Component            │  │
│  │  - Context Management UI      │  │
│  │  - Task Input Form            │  │
│  │  - Prompt Display             │  │
│  │  - Statistics Dashboard       │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      API Client (Axios)       │  │
│  │  - HTTP request handling      │  │
│  │  - Type-safe API calls        │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      TypeScript Types         │  │
│  │  - ContextUnit                │  │
│  │  - GeneratedPrompt            │  │
│  │  - TaskRequest                │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 2. Backend (FastAPI + Python)

```
┌─────────────────────────────────────┐
│        FastAPI Application          │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │      REST API Endpoints       │  │
│  │                               │  │
│  │  POST   /contexts             │  │
│  │  GET    /contexts             │  │
│  │  GET    /contexts/{id}        │  │
│  │  PUT    /contexts/{id}        │  │
│  │  DELETE /contexts/{id}        │  │
│  │  POST   /generate-prompt      │  │
│  │  GET    /stats                │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      Business Logic           │  │
│  │                               │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Relevance Engine       │  │  │
│  │  │  - Embeddings           │  │  │
│  │  │  - Similarity scoring   │  │  │
│  │  │  - Keyword matching     │  │  │
│  │  └─────────────────────────┘  │  │
│  │                               │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Prompt Composer        │  │  │
│  │  │  - Context aggregation  │  │  │
│  │  │  - Prompt formatting    │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      Data Models              │  │
│  │  - ContextUnit (Pydantic)     │  │
│  │  - Validation schemas         │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 3. Storage Layer

```
┌─────────────────────────────────────┐
│     ContextStoreInterface (ABC)     │
├─────────────────────────────────────┤
│  Abstract methods:                  │
│  - add(context, embedding)          │
│  - get(context_id)                  │
│  - list_all(include_superseded)     │
│  - update(context_id, updates)      │
│  - delete(context_id)               │
│  - supersede(old_id, new_id)        │
│  - get_embedding(context_id)        │
│  - update_embedding(context_id, emb)│
│  - list_with_embeddings()           │
└─────────────────────────────────────┘
            │
            │ implements
    ┌───────┴────────┐
    │                │
┌───▼────────┐  ┌───▼────────────────┐
│ ContextStore│  │ DatabaseContextStore│
│ (In-Memory) │  │  (PostgreSQL/SQLite)│
└─────────────┘  └─────────────────────┘
```

#### In-Memory Storage
- Fast, ephemeral storage
- Uses Python dictionaries
- Good for development/testing

#### Database Storage
- Persistent storage with SQLAlchemy 2.0
- Supports PostgreSQL (with pgvector) or SQLite
- Automatic session management
- Context manager handles commits/rollbacks          │
│  - get(id)                          │
│  - list_all()                       │
│  - update(id, updates)              │
│  - delete(id)                       │
│  - supersede(old_id, new_context)   │
└─────────────────────────────────────┘
```

## Data Flow

### Creating a Context Unit

```
User Input (Frontend)
    ↓
API Request (POST /contexts)
    ↓
FastAPI Endpoint
    ↓
Create ContextUnit model
    ↓
Generate embedding (sentence-transformers)
    ↓
Store in ContextStore
    ↓
Return ContextUnit (JSON)
    ↓
Update UI
```

### Generating a Prompt

```
User enters task (Frontend)
    ↓
API Request (POST /generate-prompt)
    ↓
FastAPI Endpoint
    ↓
Relevance Engine
    ├─ Generate task embedding
    ├─ Compute similarities
    ├─ Apply keyword matching
    └─ Rank contexts by relevance
    ↓
Prompt Composer
    ├─ Group contexts by type
    ├─ Format with confidence indicators
    ├─ Add task description
    └─ Add LLM instructions
    ↓
Return GeneratedPrompt (JSON)
    ↓
Display in UI
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Web Server**: Uvicorn
- **Data Validation**: Pydantic 2.5.3
- **Embeddings**: sentence-transformers 2.3.1
- **Vector Operations**: NumPy 1.26.3
- **ML Framework**: PyTorch 2.1.2

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 4.9.5
- **HTTP Client**: Axios 1.6.5
- **Build Tool**: react-scripts 5.0.1
- **Styling**: CSS3

## Key Design Decisions

### 1. In-Memory Storage
**Why**: Simplifies MVP, no database setup required
**Trade-off**: Data is not persistent across restarts
**Future**: Replace with PostgreSQL + pgvector

### 2. Local Embeddings
**Why**: No external API dependencies, faster, private
**Trade-off**: Larger model size, initial download
**Model**: all-MiniLM-L6-v2 (384 dimensions, 80MB)

### 3. Confidence Scoring
**Why**: Allows uncertainty representation
**Usage**: Multiplied with similarity score in relevance ranking
**Range**: 0.0 (uncertain) to 1.0 (certain)

### 4. Context Superseding
**Why**: Enables versioning without data loss
**Implementation**: Old context marked as "superseded", linked to new one
**Benefit**: Audit trail of how context evolved

### 5. Dual Ranking Strategy
**Why**: Combines semantic and keyword matching
**Semantic**: Captures meaning and intent
**Keyword**: Ensures tag matches and explicit references
**Weight**: 70% semantic, 30% keyword (configurable)

## API Design

### RESTful Principles
- **Resources**: Contexts as primary resource
- **HTTP Methods**: Standard CRUD operations
- **Status Codes**: Proper use of 2xx, 4xx, 5xx
- **Content Type**: JSON for all requests/responses

### Endpoint Design
```
/contexts           - Collection endpoint
/contexts/{id}      - Individual resource
/generate-prompt    - Action endpoint
/stats              - Analytics endpoint
```

## Security Considerations (Future)

Current MVP has no authentication. For production:

1. **Authentication**: JWT tokens or OAuth2
2. **Authorization**: User-specific contexts
3. **Rate Limiting**: Prevent API abuse
4. **Input Validation**: Already using Pydantic
5. **CORS**: Currently allows all origins (restrict in production)
6. **HTTPS**: Use TLS in production

## Scalability Considerations (Future)

Current MVP is single-threaded. For scale:

1. **Database**: PostgreSQL with connection pooling
2. **Vector Search**: pgvector or Pinecone
3. **Caching**: Redis for frequently accessed contexts
4. **Async**: FastAPI already supports async
5. **Load Balancing**: Multiple backend instances
6. **CDN**: For frontend static assets

## Performance

### Backend
- **Embedding Generation**: ~50-100ms per text
- **Similarity Search**: O(n) where n = number of contexts
- **API Response**: <200ms for typical operations

### Frontend
- **Initial Load**: ~2-3 seconds
- **Context Operations**: <100ms
- **Prompt Generation**: ~500ms-1s (includes embedding + ranking)

## Testing Strategy

### Backend
- **Unit Tests**: Models, storage, relevance engine
- **Integration Tests**: API endpoints
- **Load Tests**: Stress test with many contexts

### Frontend
- **Component Tests**: React Testing Library
- **E2E Tests**: Cypress or Playwright
- **Type Safety**: TypeScript compilation

## Monitoring (Future)

1. **Logging**: Structured logs with timestamps
2. **Metrics**: Request counts, latency, errors
3. **Tracing**: Request flow across components
4. **Alerts**: Error rates, performance degradation

## Deployment Options

### Development
```bash
./start.sh  # Runs both backend and frontend
```

### Production (Future)
- **Backend**: Docker container + Gunicorn/Uvicorn
- **Frontend**: Static build deployed to CDN
- **Database**: Managed PostgreSQL
- **Hosting**: AWS, GCP, or Heroku

## File Size Estimates

```
Backend:
- Python code: ~15 KB
- Dependencies: ~500 MB (includes PyTorch)
- Model (cached): ~80 MB

Frontend:
- TypeScript code: ~20 KB
- Dependencies: ~200 MB
- Production build: ~500 KB (gzipped)
```

## API Response Examples

### Create Context
**Request:**
```json
POST /contexts
{
  "type": "preference",
  "content": "I prefer Python over JavaScript",
  "confidence": 0.9,
  "tags": ["programming", "languages"]
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "preference",
  "content": "I prefer Python over JavaScript",
  "confidence": 0.9,
  "created_at": "2026-01-07T10:30:00Z",
  "last_used": null,
  "source": "manual",
  "tags": ["programming", "languages"],
  "status": "active",
  "superseded_by": null
}
```

### Generate Prompt
**Request:**
```json
POST /generate-prompt
{
  "task": "Write a sorting algorithm",
  "max_context_units": 3
}
```

**Response:**
```json
{
  "original_task": "Write a sorting algorithm",
  "relevant_context": [
    {
      "context_unit": {
        "id": "...",
        "type": "preference",
        "content": "I prefer Python over JavaScript",
        "confidence": 0.9,
        ...
      },
      "relevance_score": 0.87
    },
    ...
  ],
  "generated_prompt": "# Context\n\n## Preferences\n...",
  "timestamp": "2026-01-07T10:31:00Z"
}
```

## Conclusion

ContextPilot MVP demonstrates a clean, modular architecture that:
- ✅ Separates concerns (frontend, backend, storage)
- ✅ Uses modern technologies (FastAPI, React, Transformers)
- ✅ Provides a solid foundation for future enhancements
- ✅ Focuses on core value: context-aware prompts

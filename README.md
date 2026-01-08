# 🧭 ContextPilot

An AI-powered personal context engine that automatically builds and maintains a structured "memory" of a user's projects, decisions, preferences, and knowledge—then injects the right context into future AI prompts, emails, documents, or code tasks.

## 🎯 What is ContextPilot?

Most AI tools are stateless—they forget context between sessions. ContextPilot solves this by:

- **Storing structured context** (preferences, decisions, goals, facts) with versioning
- **Ranking context by relevance** using semantic embeddings
- **Generating optimized prompts** that automatically include the right context
- **Providing a clean UI** to manage your personal knowledge base

## ✨ Features

- ✅ **CRUD operations** for context units
- ✅ **Persistent storage** with SQLite or PostgreSQL + pgvector
- ✅ **AI integration** with OpenAI (GPT-4) and Anthropic (Claude)
- ✅ **Conversation history** with automatic persistence
- ✅ **Semantic search** using sentence-transformers embeddings
- ✅ **Embedding caching** for faster similarity searches
- ✅ **Response caching** for improved API performance
- ✅ **Confidence scoring** and versioning
- ✅ **Relevance engine** that ranks contexts by task relevance
- ✅ **Prompt composer** that generates LLM-ready prompts
- ✅ **Clean React UI** for managing context and viewing prompts
- ✅ **RESTful API** with FastAPI and OpenAPI documentation
- ✅ **Security features** - API key auth, input validation, CORS, rate limiting
- ✅ **Request tracking** with unique IDs and timing
- ✅ **Structured logging** with JSON output option
- ✅ **Database migrations** with Alembic
- ✅ **No external dependencies** for embeddings (uses local models)
- ✅ **Context Import/Export** - JSON/CSV export and JSON import functionality
- ✅ **Advanced Filtering** - Search by type, tags, content, and status
- ✅ **Context Templates** - Quick creation with 6 pre-defined templates
- ✅ **Mobile Responsive UI** - Optimized for mobile devices
- ✅ **Enhanced UX** - Loading states, smooth transitions, and improved interactions

## 🏗️ Architecture

```
┌─────────────────┐
│   React UI      │  ← User Interface
│  (TypeScript)   │
└────────┬────────┘
         │
    HTTP REST API
         │
┌────────▼────────┐
│  FastAPI Server │  ← Backend
│                 │
│  ┌───────────┐  │
│  │ Storage   │  │  ← SQLite/PostgreSQL or in-memory
│  │ (Database)│  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │ Relevance │  │  ← Embedding-based ranking
│  │  Engine   │  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │  Prompt   │  │  ← Context composition
│  │ Composer  │  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │AI Service │  │  ← OpenAI / Anthropic
│  └───────────┘  │
└─────────────────┘
```

## 📁 Project Structure

```
ContextPilot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic data models
│   ├── storage.py           # In-memory context store
│   ├── relevance.py         # Relevance ranking engine
│   ├── composer.py          # Prompt composition
│   ├── example_data.py      # Example context units
│   ├── test_api.py          # Test script
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # Backend docs
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── App.css          # Styles
│   │   ├── api.ts           # API client
│   │   ├── types.ts         # TypeScript types
│   │   └── index.tsx        # Entry point
│   ├── public/
│   │   └── index.html       # HTML template
│   ├── package.json         # Node dependencies
│   └── tsconfig.json        # TypeScript config
├── demo.sh                  # Demo script
├── CONCEPT.txt              # Original concept document
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database URL
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the server with example data (optional):
```bash
python -c "from example_data import load_example_data; load_example_data()" && python main.py
```

Or run without example data:
```bash
python main.py
```

The backend will be available at **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

> **Note**: For production deployment with PostgreSQL and pgvector, see [DATABASE.md](backend/docs/DATABASE.md)

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at **http://localhost:3000**

## 📝 Usage Examples

### 1. Using the Web UI

1. Open http://localhost:3000
2. Add context units (preferences, decisions, facts, goals)
3. Enter a task in the "Generate Prompt" section
4. View the generated prompt with relevant context
5. Copy the prompt to use with any LLM
6. **NEW**: Use the AI Chat feature to get instant AI responses with context

### 2. Using the API

**Create a context:**
```bash
curl -X POST http://localhost:8000/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "type": "preference",
    "content": "I prefer functional programming style",
    "confidence": 0.9,
    "tags": ["programming", "style"]
  }'
```

**List contexts:**
```bash
curl http://localhost:8000/contexts
```

**Generate a prompt:**
```bash
curl -X POST http://localhost:8000/generate-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a function to sort a list",
    "max_context_units": 5
  }'
```

**Ask AI with context (NEW):**
```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Explain the main purpose of this codebase",
    "max_context_units": 5,
    "provider": "openai",
    "model": "gpt-4-turbo-preview"
  }'
```

**View conversation history (NEW):**
```bash
curl http://localhost:8000/ai/conversations
```

### 3. Example Generated Prompt

**Task:** "Write a Python function to calculate fibonacci numbers"

**Generated Prompt:**
```
# Context

## Preferences
- [✓] I prefer concise, technical explanations without excessive verbosity
  (Tags: communication, style, technical)
- [✓] I like code examples in Python and TypeScript
  (Tags: programming, languages)

## Goals
- [✓] Building an AI-powered context management system called ContextPilot
  (Tags: project, ai, context)

## Decisions
- [✓] Using FastAPI for backend instead of Django for better async support
  (Tags: architecture, backend, fastapi)

## Facts
- [✓] I have experience with vector databases and embeddings
  (Tags: skills, ai, embeddings)

# Task

Write a Python function to calculate fibonacci numbers

# Instructions
Please complete the task above, taking into account the provided context.
Align your response with the stated preferences, goals, and decisions.
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python test_api.py
```

### Run Demo Script
```bash
| POST | `/ai/chat` | **NEW**: Generate AI response with context |
| GET | `/ai/conversations` | **NEW**: List conversation history |
| GET | `/ai/conversations/{id}` | **NEW**: Get specific conversation |

For detailed API documentation, see the interactive docs at `/docs` when the server is running.
chmod +x demo.sh
./demo.sh
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/stats` | Get statistics |
| POST | `/contexts` | Create context unit |
| GET | `/contexts` | List all contexts |
| GET | `/contexts/{id}` | Get specific context |
| PUT | `/contexts/{id}` | Update context |
| DELETE | `/contexts/{id}` | Delete context |
| POST | `/generate-prompt` | Generate contextualized prompt |
| POST | `/generate-prompt/compact` | Generate compact prompt |

## 📊 Data Model

### ContextUnit
```typescript
{
  id: string;                    // Unique ID
  type: "preference" | "decision" | "fact" | "goal";
  content: string;               // Natural language description
  confidence: number;            // 0.0 - 1.0
  created_at: string;            // ISO timestamp
  last_used: string | null;      // ISO timestamp
  source: string;                // "manual" or "extracted"
  tags: string[];                // Array of tags
  status: "active" | "superseded";
  superseded_by: string | null;  // ID of replacing context
}
```
SQLAlchemy 2.0 (ORM and database toolkit)
- PostgreSQL / SQLite (persistent storage)
- pgvector (vector similarity search)
- OpenAI API (GPT-4 integration)
- Anthropic API (Claude integration)
- sentence-transformers (embeddings)
- Pydantic (data validation)
- NumPy (vector operations)

**Frontend:**
- React 18
- TypeScript
- Axios (HTTP client)
- CSS3 (styling)

## 📚 Documentation

- **[Database Setup](backend/docs/DATABASE.md)**: SQLite and PostgreSQL configuration
- **[AI Integration](backend/docs/AI_INTEGRATION.md)**: OpenAI and Anthropic setup
- **[API Reference](http://localhost:8000/docs)**: Interactive API documentation (when server is running)

## 🔮 Future Enhancements

- [x] Persistent storage (PostgreSQL + pgvector) ✅
- [x] ChatGPT/Claude API integration ✅
- [ ] Automatic context extraction from documents
- [ ] Context decay and reinforcement learning
- [ ] Conflict detection between contexts
- [ ] Browser extension for automatic context capture
- [ ] IDE plugin integration
- [ ] Export/import functionality
- [ ] Advanced search and filtering
- [ ] Analytics dashboard
- [ ] Streaming AI responses
- [ ] Multi-turn conversationsor automatic context capture
- [ ] IDE plugin integration
- [ ] ChatGPT/Claude API integration
- [ ] Export/import functionality
- [ ] Search and filtering
- [ ] Analytics dashboard

## 🤝 Contributing

This is an MVP. Contributions are welcome! Areas for improvement:

1. **Storage**: Replace in-memory store with persistent database
2. **Embeddings**: Add support for other embedding models
3. **UI**: Enhance the interface with better visualizations
4. **Testing**: Add unit tests and integration tests
5. **Documentation**: Improve API documentation

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI and React
- Embeddings powered by sentence-transformers
- Inspired by the need for context-aware AI interactions

---

**Built with ❤️ for better AI conversations**

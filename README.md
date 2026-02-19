# 🧭 ContextPilot

A multi-model AI chat interface that lets you create, organize, and inject structured context into conversations with different AI models (OpenAI, Anthropic, Ollama). Maintain your project knowledge, preferences, and decisions in organized contexts that can be selectively applied to enhance AI interactions.

## 🎯 What is ContextPilot?

Most AI tools are stateless—they forget context between sessions. ContextPilot solves this by:

- **Storing structured context** (preferences, decisions, goals, facts) with versioning
- **Ranking context by relevance** using semantic embeddings
- **Generating optimized prompts** that automatically include the right context
- **Providing a clean UI** to manage your personal knowledge base

## ✨ Features

### Core Functionality
- ✅ **CRUD operations** for context units with versioning
- ✅ **Persistent storage** with SQLite or PostgreSQL + pgvector
- ✅ **AI integration** with OpenAI (GPT-4, GPT-4o), Anthropic (Claude), and Ollama (local models)
- ✅ **Dynamic model discovery** - Automatically detects available models from each provider
- ✅ **Model validation** - Only shows working, current models in the UI
- ✅ **Semantic search** using sentence-transformers embeddings
- ✅ **Embedding caching** for faster similarity searches
- ✅ **Response caching** for improved API performance
- ✅ **Confidence scoring** and context versioning
- ✅ **Relevance engine** that ranks contexts by task relevance
- ✅ **Prompt composer** that generates LLM-ready prompts

### Chat & Conversations
- ✅ **Minimal chat-style interface** with right-aligned user messages and clean assistant rows
- ✅ **Conversation history** with automatic persistence
- ✅ **Smart context management** - sends contexts once per conversation
- ✅ **Interaction log output** - Shows user↔frontend and frontend↔backend events in a dedicated panel
- ✅ **Newest-first interaction timeline** - Latest log entries are displayed at the top
- ✅ **Auto-scroll** to latest messages
- ✅ **Typing indicators** for AI responses
- ✅ **Context refresh control** for explicit context reloading
- ✅ **New conversation** button to start fresh chats
- ✅ **Markdown image support** - Automatically renders images from `![alt](url)` syntax
- ✅ **Image error handling** - Displays helpful warnings when images fail to load
- ✅ **Immediate message display** - Shows user messages before API response
- ✅ **Concurrent request prevention** - Disables send button during API calls
- ✅ **Smart truncation handling** - Shows detailed messages for truncated responses with token counts
- ✅ **Model attribution** - Shows which AI model generated each response for transparency

### UI/UX
- ✅ **Modern Interface Design** - Clean, professional layout with brand identity
- ✅ **Simplified Navigation** - Streamlined interface with intuitive return navigation
- ✅ **Inline status in header** - Success/error status appears beside the settings button
- ✅ **Side-by-side settings layout** - Provider configuration and general defaults are shown together
- ✅ **Dark mode support** - Full interface dark theme with persisted preference
- ✅ **2-Column Manage Layout** - Organized context management with responsive grid design
- ✅ **Custom Branding** - Distinctive "by B" signature with custom fuzzy B logo
- ✅ **Mobile Responsive** - Optimized for all screen sizes with proper breakpoints
- ✅ **Enhanced UX** - Loading states, smooth transitions, and improved interactions
- ✅ **Full-width layout** utilizing entire browser window
- ✅ **Input clearing** - Automatically clears text box on message send
- ✅ **Settings Management** - Configure API keys and AI parameters directly in the UI
- ✅ **Flexible token limits** - Supports up to 16,000 tokens (default: 4000)
- ✅ **Context Import/Export** - JSON/CSV export and JSON import functionality
- ✅ **Advanced Filtering** - Search by type, tags, content, and status
- ✅ **Context Templates** - Quick creation with 6 pre-defined templates
- ✅ **Dynamic Model Management** - Automatic model discovery and caching for optimal performance

### Technical Features
- ✅ **RESTful API** with FastAPI and OpenAPI documentation
- ✅ **Security features** - API key auth, input validation, CORS, rate limiting
- ✅ **Request tracking** with unique IDs and timing
- ✅ **Structured logging** with JSON output option
- ✅ **Database migrations** with Alembic
- ✅ **No external dependencies** for embeddings (uses local models)
- ✅ **Provider-specific settings** - Override temperature, context window, and API params per provider
- ✅ **Model synchronization** - Keep frontend/backend models in sync automatically
- ✅ **Latest models** - GPT-5, GPT-5.2, Claude 4.5, Claude Haiku 4.5 support

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
│  │Modular AI │  │  ← OpenAI / Anthropic / Ollama
│  │ Providers │  │     (Pluggable architecture)
│  └───────────┘  │
└─────────────────┘
```

### 🔌 Modular Provider Architecture

ContextPilot now features a **modular, plugin-like architecture** for LLM integrations:

- **Extensible Design**: Each provider (OpenAI, Anthropic, Ollama) is a separate module
- **Provider-Specific Features**: Auto-pull for Ollama, cost estimation for OpenAI/Anthropic
- **Easy to Add**: Add new providers without modifying core code
- **Health Monitoring**: Built-in health checks and capability detection
- **Type-Safe**: Full type hints and clear interfaces

**Documentation:**
- [PROVIDER_ARCHITECTURE.md](docs/PROVIDER_ARCHITECTURE.md) - Complete architecture guide
- [PROVIDER_INTEGRATION.md](docs/PROVIDER_INTEGRATION.md) - Migration and integration guide

## 📁 Project Structure

```
ContextPilot/
├── backend/                 # FastAPI backend server
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Pydantic data models
│   ├── db_models.py         # SQLAlchemy database models
│   ├── storage.py           # In-memory context store
│   ├── db_storage.py        # Database storage implementation
│   ├── storage_interface.py # Storage abstraction layer
│   ├── relevance.py         # Semantic search & ranking
│   ├── composer.py          # Prompt composition engine
│   ├── ai_service.py        # Legacy AI service (still supported)
│   ├── ai_service_modular.py# New modular AI service
│   ├── providers/           # 🆕 Modular LLM provider system
│   │   ├── __init__.py      # Provider exports
│   │   ├── base_provider.py # Abstract base class & interfaces
│   │   ├── provider_registry.py # Provider registry & factory
│   │   ├── openai_provider.py   # OpenAI integration
│   │   ├── anthropic_provider.py # Anthropic/Claude integration
│   │   ├── ollama_provider.py   # Ollama local LLM integration
│   │   └── README.md        # Provider documentation
│   ├── config.py            # Configuration management
│   ├── security.py          # Authentication & validation
│   ├── validators.py        # Dynamic model validation
│   ├── database.py          # Database session management
│   ├── valid_models.json    # Dynamic model validation rules
│   ├── alembic/             # Database migration scripts
│   ├── test_*.py            # Comprehensive test suite (205 tests)
│   ├── test_providers.py    # 🆕 Provider system tests (22 tests)
│   ├── example_providers.py # 🆕 Provider usage examples
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # Backend documentation
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── AppContext.tsx   # React context & state management
│   │   ├── ContextTemplates.tsx # Template creation component
│   │   ├── ContextTools.tsx # Import/export & filtering tools
│   │   ├── api.ts           # API client with all endpoints
│   │   ├── types.ts         # TypeScript type definitions
│   │   ├── model_options.json # Dynamic model configuration
│   │   └── main.tsx         # React entry point
│   ├── index.html           # Vite HTML entry point
│   ├── package.json         # Node.js dependencies
│   └── tsconfig.json        # TypeScript configuration
├── docs/                    # Documentation (see below)
├── bin/                     # Utility scripts
│   ├── discover_models.py   # Model discovery script
│   ├── refresh_models.py    # Startup model refresh integration
│   ├── update_models.sh     # Manual model update script
│   └── sync_models.py       # Model synchronization utility
├── test/                    # Test and demo scripts
│   ├── test_dynamic_models.py
│   ├── demo_dynamic_models.py
│   ├── test_model_*.py      # Model validation tests
│   └── demo.sh              # API demo script
├── LICENSE                  # MIT License
├── THIRD_PARTY_NOTICES      # Third-party dependency licenses
├── QUICKSTART.md            # Quick reference guide
├── setup.sh                 # Automated environment setup
├── start.sh                 # Start both backend & frontend (with auto-setup)
├── stop.sh                  # Stop all services
├── start-backend.sh         # Start backend only
├── start-frontend.sh        # Start frontend only
├── demo.sh                  # Demo with sample data
├── CONCEPT.txt              # Original concept document
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Option 1: Automated Setup (Recommended)

The easiest way to get started is using the automated setup script:

```bash
./setup.sh
```

This script will:
- ✅ Check all prerequisites (Python 3, Node.js)
- ✅ Create and configure virtual environment
- ✅ Install all backend dependencies
- ✅ Initialize the database
- ✅ Install all frontend dependencies
- ✅ Detect and fix common issues (broken symlinks, missing packages)

Then start the application:

```bash
./start.sh
```

This will:
- ✅ Automatically run setup if needed
- ✅ Start the backend server on http://localhost:8000
- ✅ Start the frontend development server on http://localhost:3000
- ✅ Open the application in your browser
- ✅ Provide health check verification

To stop all services:

```bash
./stop.sh
```

### Option 2: Manual Setup

#### Backend Setup

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

#### Frontend Setup

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
npm run dev
```

The frontend will be available at **http://localhost:3000**

## 📝 Usage Examples

### 1. Using the Web UI

1. Open http://localhost:3000
2. **Configure API Keys & Provider Settings**: Click the ⚙️ settings button to:
   - Configure your OpenAI, Anthropic, or Ollama API keys
   - Set provider-specific defaults (model, temperature, max tokens)
   - Override global settings per provider for fine-tuned control
   - For Ollama: Set the base URL (default: http://localhost:11434)
3. **Add Context**: Add context units (preferences, decisions, facts, goals) using templates or manual entry in the left sidebar
4. **Start a Chat**: 
   - Select a previous conversation from the list, or
   - Click "New Conversation" to start fresh
5. **Chat with AI**: Enter your question/task in the chat interface
   - Relevant contexts are automatically included in the first message
   - Follow-up messages continue the conversation without re-sending contexts
   - Click the "Refresh Contexts" toggle if you want to reload contexts in a follow-up
6. **View History**: All conversations are saved and can be accessed from the left sidebar
7. **Monitor Interactions**: Use the Interaction Log panel (below conversations) to inspect user actions, backend requests, and status outcomes in reverse-chronological order
8. **Manage Contexts**:
  - View all your contexts in the right sidebar
  - Use filters to find specific contexts
  - Export/import contexts as JSON or CSV
9. **Generate Standalone Prompts**: Use the middle column's "Generate Prompt" section to create prompts for use in other tools

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

**Ask AI with context:**
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

**Continue a conversation (with conversation_id):**
```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Can you elaborate on the architecture?",
    "max_context_units": 0,
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "conversation_id": "abc123"
  }'
```

**View conversation history:**
```bash
curl http://localhost:8000/ai/conversations
```

**Get specific conversation:**
```bash
curl http://localhost:8000/ai/conversations/{conversation_id}
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

## ⚙️ Configuration

### Settings Management

ContextPilot provides a settings UI (⚙️ button) where you can configure:

#### AI Configuration
- **OpenAI API Key**: Required for using GPT models
- **OpenAI Base URL**: Optional override for compatible gateways
- **OpenAI Overrides**: Default model, temperature, top_p, max tokens
- **Anthropic API Key**: Required for using Claude models
- **Anthropic Overrides**: Default model, temperature, top_p, top_k, max tokens
- **Ollama Base URL**: Local Ollama server endpoint (default: http://localhost:11434)
- **Ollama Overrides**: Default model, temperature, top_p, num_predict, num_ctx, keep_alive
- **Default AI Provider**: Choose between `openai`, `anthropic`, or `ollama`
- **Default AI Model**: Set default model
  - OpenAI: `gpt-5.2`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, etc.
  - Anthropic: `claude-opus-4-5-20251101`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`, etc.
  - Ollama: `llama3.2`, `mistral`, `codellama`, `phi3`, etc.
- **Temperature**: Control randomness (0.0-2.0, default: 1.0)
- **Max Tokens**: Maximum response length (1-16000, default: 4000)
  - Increase this if you're getting truncated responses
  - For image-heavy responses, consider 8000+ tokens

#### Local Models with Ollama

ContextPilot supports running AI models locally using [Ollama](https://ollama.ai):

1. **Install Ollama**: Download from https://ollama.ai
2. **Pull a model**: `ollama pull llama3.2` (or mistral, codellama, etc.)
3. **Start Ollama**: `ollama serve` (runs on http://localhost:11434 by default)
4. **Configure ContextPilot**: 
   - Open Settings (⚙️ button)
   - Set Ollama Base URL (default works if Ollama is running locally)
   - Select "Ollama (Local)" as provider
   - Choose your downloaded model

**Benefits of Local Models:**
- ✅ No API keys required
- ✅ Complete privacy - no data sent to external services
- ✅ No API costs
- ✅ Works offline
- ✅ Faster responses (no network latency)

**Supported Ollama Models:**
- `llama3.2` - Meta's latest Llama model
- `llama3.1` - Previous Llama version
- `mistral` - Mistral AI's model
- `codellama` - Specialized for code generation
- `phi3` - Microsoft's efficient model

**Automatic Model Download:**
If you select a model that hasn't been downloaded yet, ContextPilot will automatically pull it for you. The first request may take 1-5 minutes depending on model size, but subsequent requests will be instant.

#### Settings API

You can also configure settings via API:

```bash
# Get current settings
curl http://localhost:8000/settings

# List providers and model metadata
curl http://localhost:8000/providers

# Update settings
curl -X POST http://localhost:8000/settings \
  -H "Content-Type: application/json" \
  -d '{
    "openai_api_key": "sk-...",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_default_model": "gpt-4o",
    "openai_temperature": 0.7,
    "openai_top_p": 0.9,
    "openai_max_tokens": 2000,
    "anthropic_api_key": "sk-ant-...",
    "anthropic_default_model": "claude-3-5-sonnet-20241022",
    "anthropic_temperature": 0.7,
    "anthropic_top_p": 0.9,
    "anthropic_top_k": 40,
    "anthropic_max_tokens": 2000,
    "ollama_base_url": "http://localhost:11434",
    "ollama_default_model": "llama3.2",
    "ollama_temperature": 0.7,
    "ollama_top_p": 0.9,
    "ollama_num_predict": 2000,
    "ollama_num_ctx": 4096,
    "ollama_keep_alive": "5m",
    "default_ai_provider": "ollama",
    "default_ai_model": "llama3.2",
    "ai_temperature": 0.7,
    "ai_max_tokens": 8000
  }'
```

### Dynamic Model Discovery

ContextPilot features an advanced dynamic model discovery system that automatically detects available AI models from each provider, ensuring you always have access to the latest and working models.

#### How It Works

- **OpenAI**: Fetches available chat models via API (when API key is configured)
- **Anthropic**: Fetches available models via `client.models.list()` API (when API key is configured)
- **Ollama**: Automatically detects locally installed models

#### Key Benefits

- ✅ **Always Current**: Shows only working, available models
- ✅ **Automatic Updates**: Refreshes model lists daily
- ✅ **Local Model Detection**: Finds Ollama models automatically
- ✅ **Performance Optimized**: 24-hour caching to minimize API calls
- ✅ **Robust Fallbacks**: Works even when APIs are unavailable

#### Manual Model Discovery

Refresh available models manually:

```bash
# Discover and cache all available models
python3 bin/discover_models.py

# Force refresh (ignore cache)
python3 bin/refresh_models.py --force

# Quick status check
python3 test/demo_dynamic_models.py

# Verify model synchronization
python3 bin/sync_models.py --check
```

#### Scheduled Updates

Set up automatic daily model discovery:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 6 AM)
0 6 * * * /path/to/ContextPilot/bin/update_models.sh
```

#### Current Model Status

As of last discovery, ContextPilot supports:
- **OpenAI**: GPT-5.2, GPT-5, GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude 4.5 (Opus, Sonnet, Haiku), Claude 4.1 Opus, Claude 4.0, Claude 3 Haiku
- **Ollama**: Automatically detected local models (e.g., llama3.2:latest)

> **Note**: Model availability depends on your API access and local Ollama installations. The system automatically updates these lists to match your actual capabilities.

### Image Display

The chat interface supports markdown images using the syntax: `![alt text](image_url)`

When AI responses include image markdown:
- Images are automatically rendered inline
- Failed image loads show a helpful warning with a link to the image URL
- This is useful for asking AI to generate or reference images

### Database Backup & Restore

To prevent accidental data loss, use the provided backup scripts:

```bash
# Create a backup (stored in backend/backups/)
cd backend
./backup_db.sh

# Restore from a backup
./restore_db.sh
```

**Automatic backup retention**: The backup script keeps the last 10 backups automatically.

**Before database maintenance**: Always create a backup before:
- Running database migrations
- Reinitializing the database
- Upgrading the application
- Testing database-related changes

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python -m pytest  # Run all tests
python -m pytest --ignore=test_integration.py  # Skip integration tests
```

Backend status:
- ✅ 207 collected (`206 passed, 1 skipped` in local run)
- ✅ API, storage, validators, settings, providers, and migration coverage
- ✅ Attribution integrity checks ensure `/ai/chat` returns executed provider/model metadata

### Run Frontend Checks and Tests
```bash
cd frontend
npm run type-check
npm run lint
npm run build
npm run test:quick
npm run test:coverage
npm run e2e
```

Frontend status:
- ✅ 91 unit/integration tests passing
- ✅ 16 Playwright E2E tests passing
- ✅ Coverage: 90.46% statements / 90.46% lines
- ✅ App surface coverage: 86.54% statements/lines in `App.tsx`
- ✅ Regression test prevents UI from showing requested model when backend reports a different executing model

### Run Demo Script
```bash
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
| POST | `/ai/chat` | Generate AI response with context |
| GET | `/ai/conversations` | List conversation history |
| GET | `/ai/conversations/{id}` | Get specific conversation with messages |
| DELETE | `/ai/conversations/{id}` | Delete conversation |

For detailed API documentation, see the interactive docs at `/docs` when the server is running.

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
- **[Model Discovery](docs/MODEL_DISCOVERY.md)**: Dynamic model discovery system
- **[API Reference](http://localhost:8000/docs)**: Interactive API documentation (when server is running)

## 🔮 Future Enhancements

- [x] Persistent storage (PostgreSQL + pgvector) ✅
- [x] ChatGPT/Claude API integration ✅
- [x] Export/import functionality ✅
- [x] Advanced search and filtering ✅
- [x] Chat-style interface with conversation history ✅
- [x] Smart context management (one-time sending per conversation) ✅
- [ ] Automatic context extraction from documents
- [ ] Context decay and reinforcement learning
- [ ] Conflict detection between contexts
- [ ] Browser extension for automatic context capture
- [ ] IDE plugin integration
- [ ] Analytics dashboard
- [ ] Streaming AI responses
- [ ] Multi-user support with authentication

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

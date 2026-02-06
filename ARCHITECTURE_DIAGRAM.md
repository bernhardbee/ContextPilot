# ContextPilot - Detailed Architecture Diagram

## 1. SYSTEM-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                               │
│  (Chrome, Firefox, Safari - HTTP/WebSocket)                         │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                    HTTP │ 5173 (dev) / 3000 (prod)
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────────┐       ┌─────────────────────┐
│   FRONTEND SERVER    │       │  VITE DEV SERVER    │
│   (Vite 7.3.1)       │       │  (Dev Only)         │
│   localhost:3000     │       │  localhost:5173     │
│                      │       │                     │
│  - React 18.3.1      │       │  Hot Module Reload  │
│  - TypeScript 4.9.5  │       │  Source Maps        │
│  - Axios Client      │       │  ESM Modules        │
│  - Markdown Parser   │       │                     │
└──────────────────────┘       └─────────────────────┘
        │
        │  HTTP/JSON (REST API)
        │  Port 8000
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│            BACKEND API SERVER                              │
│            (FastAPI 0.109.0)                               │
│            localhost:8000 / 0.0.0.0:8000                   │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐  │
│ │  API ROUTES                                          │  │
│ │                                                      │  │
│ │  POST   /contexts             - Create context      │  │
│ │  GET    /contexts/{id}        - Retrieve context    │  │
│ │  PUT    /contexts/{id}        - Update context      │  │
│ │  DELETE /contexts/{id}        - Delete context      │  │
│ │  GET    /contexts?search=     - List & search       │  │
│ │                                                      │  │
│ │  POST   /generate-prompt      - Generate with AI    │  │
│ │  POST   /ai-chat              - Chat endpoint       │  │
│ │  GET    /models               - List available AI   │  │
│ │  GET    /conversations/{id}   - Chat history        │  │
│ │                                                      │  │
│ │  GET    /settings             - User settings       │  │
│ │  POST   /settings             - Update settings     │  │
│ │  GET    /stats                - Usage statistics    │  │
│ │                                                      │  │
│ │  GET    /health               - Health check        │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐  │
│ │  MIDDLEWARE & UTILITIES                              │  │
│ │                                                      │  │
│ │  - CORS (Cross-Origin Resource Sharing)             │  │
│ │  - Rate Limiting (SlowAPI)                           │  │
│ │  - Request/Response Logging                          │  │
│ │  - Error Handling & Validation                       │  │
│ │  - Security (HTTPS, headers)                         │  │
│ │  - Request Tracking                                  │  │
│ └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
        │
        ├──────────────────┬──────────────────┬────────────────┐
        │                  │                  │                │
        ▼                  ▼                  ▼                ▼
   DATABASE         AI SERVICES        EXTERNAL APIs    CACHING
```

---

## 2. FRONTEND ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                     FRONTEND APPLICATION                           │
│                   (React 18.3.1 + TypeScript)                       │
│                      localhost:5173                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  VITE BUILD SYSTEM (vite.config.ts)                        │  │
│  │                                                            │  │
│  │  - Dev Server: HMR (Hot Module Replacement)               │  │
│  │  - Proxy: /api → http://localhost:8000/api               │  │
│  │  - Build Output: dist/ (optimized chunks)                 │  │
│  │  - Entry Point: index.html → src/main.tsx                │  │
│  │  - Chunk Size Warning Limit: 800KB                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▲                                       │
│                           │ imports                               │
│                           ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  APPLICATION STRUCTURE                                     │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ src/main.tsx (Entry Point)                           │ │  │
│  │  │  - React DOM Render                                  │ │  │
│  │  │  - Root Element Mounting                             │ │  │
│  │  └────────────────┬──────────────────────────────────────┘ │  │
│  │                   │ imports                                │  │
│  │  ┌────────────────▼──────────────────────────────────────┐ │  │
│  │  │ src/App.tsx (Main Component)                          │ │  │
│  │  │  - Global State Management (AppContext)              │ │  │
│  │  │  - Router/Navigation Logic                           │ │  │
│  │  │  - Layout & Styling (App.css)                        │ │  │
│  │  └────────────────┬──────────────────────────────────────┘ │  │
│  │                   │                                        │  │
│  │     ┌─────────────┴──────────────┬────────────────┐       │  │
│  │     │                            │                │       │  │
│  │     ▼                            ▼                ▼       │  │
│  │ ┌─────────────┐  ┌────────────────────┐  ┌──────────┐   │  │
│  │ │ Context     │  │ AI Integration     │  │ Settings │   │  │
│  │ │ Management  │  │ (ContextTools.tsx) │  │ Panel    │   │  │
│  │ │             │  │                    │  │          │   │  │
│  │ │ - List      │  │ - Prompt Gen       │  │ - User   │   │  │
│  │ │ - Create    │  │ - AI Chat          │  │   Config │   │  │
│  │ │ - Search    │  │ - Model Selection  │  │ - Theme  │   │  │
│  │ │ - Templates │  │ - Conversation Hist│  │ - Export │   │  │
│  │ └─────────────┘  └────────────────────┘  └──────────┘   │  │
│  │        │                  │                      │       │  │
│  │        └──────────────────┴──────────────────────┘       │  │
│  │                  All use AppContext                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  TYPESCRIPT TYPES (types.ts)                               │ │
│  │                                                            │ │
│  │  - IContext: { id, title, content, metadata, ... }        │ │
│  │  - IMessage: { role, content, timestamp, ... }            │ │
│  │  - IAIModel: { id, name, provider, available, ... }       │ │
│  │  - ISettings: { apiKey, theme, autoSave, ... }            │ │
│  │  - IStats: { totalContexts, chatsCount, ... }             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API CLIENT (api.ts) - Axios Wrapper                       │ │
│  │                                                            │ │
│  │  Base URL: http://localhost:8000/api (proxied via Vite)   │ │
│  │                                                            │ │
│  │  Methods:                                                  │ │
│  │  - getContexts(query?)                                    │ │
│  │  - getContext(id)                                         │ │
│  │  - createContext(data)                                    │ │
│  │  - updateContext(id, data)                                │ │
│  │  - deleteContext(id)                                      │ │
│  │  - generatePrompt(context)                                │ │
│  │  - chatWithAI(messages, model)                            │ │
│  │  - getAvailableModels()                                   │ │
│  │  - getConversation(id)                                    │ │
│  │  - getSettings() / updateSettings(settings)               │ │
│  │  - getStats()                                             │ │
│  │                                                            │ │
│  │  Error Handling:                                           │ │
│  │  - 4xx: Client errors (validation, not found)             │ │
│  │  - 5xx: Server errors (retry logic)                       │ │
│  │  - Network errors: User notification                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DEPENDENCIES                                              │ │
│  │                                                            │ │
│  │  - React 18.3.1: UI Framework                             │ │
│  │  - TypeScript 4.9.5: Type Safety                          │ │
│  │  - Axios 1.13.4: HTTP Client                              │ │
│  │  - React Markdown 10.1.0: Markdown Rendering              │ │
│  │  - Highlight.js 11.11.1: Code Syntax Highlighting         │ │
│  │  - Rehype Highlight 7.0.2: Markdown Code Blocks           │ │
│  │  - Remark GFM 4.0.1: GitHub Flavored Markdown            │ │
│  │  - Vite 7.3.1: Build Tool & Dev Server                   │ │
│  │  - @vitejs/plugin-react 5.1.3: React Plugin for Vite     │ │
│  │  - @types/react & @types/react-dom: TypeScript Definitions│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. BACKEND ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                      BACKEND APPLICATION                           │
│                    (FastAPI 0.109.0 + Python 3.9)                   │
│                      localhost:8000                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  APPLICATION ENTRY POINT (main.py)                         │  │
│  │                                                            │  │
│  │  - FastAPI App Initialization                             │  │
│  │  - CORS Middleware Configuration                          │  │
│  │  - Rate Limiting Setup (SlowAPI)                          │  │
│  │  - Request Logging Middleware                             │  │
│  │  - Error Handler Registration                             │  │
│  │  - Route Registration                                     │  │
│  │  - Uvicorn Server Start                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▲                                       │
│                           │ imports                               │
│          ┌────────────────┼────────────────┬─────────────┐       │
│          │                │                │             │       │
│          ▼                ▼                ▼             ▼       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────┐  │
│  │ ROUTERS      │ │ SERVICES     │ │ DATABASE │ │ UTILITIES  │  │
│  │              │ │              │ │          │ │            │  │
│  │ /api/        │ │ AI Service   │ │ Models   │ │ Validators │  │
│  │ /contexts    │ │ Embedding    │ │ Storage  │ │ Security   │  │
│  │ /chat        │ │ Response     │ │ Session  │ │ Logger     │  │
│  │ /models      │ │ Cache        │ │ Engine   │ │ Config     │  │
│  │ /settings    │ │              │ │          │ │            │  │
│  │ /stats       │ │              │ │          │ │            │  │
│  └──────────────┘ └──────────────┘ └──────────┘ └────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ROUTER DETAILS                                            │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Context Management Routes (POST /api/contexts)       │ │  │
│  │  │                                                      │ │  │
│  │  │ POST   /api/contexts              [Create]          │ │  │
│  │  │   Payload: { title, content, metadata }             │ │  │
│  │  │   Response: { id, created_at, ... }                 │ │  │
│  │  │                                                      │ │  │
│  │  │ GET    /api/contexts              [List/Search]     │ │  │
│  │  │   Query: ?search=term&limit=10&offset=0             │ │  │
│  │  │   Response: [{ contexts... }]                        │ │  │
│  │  │                                                      │ │  │
│  │  │ GET    /api/contexts/{id}         [Retrieve]        │ │  │
│  │  │   Response: { id, title, content, ... }             │ │  │
│  │  │                                                      │ │  │
│  │  │ PUT    /api/contexts/{id}         [Update]          │ │  │
│  │  │   Payload: { title, content, metadata }             │ │  │
│  │  │   Response: { id, updated_at, ... }                 │ │  │
│  │  │                                                      │ │  │
│  │  │ DELETE /api/contexts/{id}         [Delete]          │ │  │
│  │  │   Response: { success: true }                        │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ AI Integration Routes                                │ │  │
│  │  │                                                      │ │  │
│  │  │ POST /api/generate-prompt                           │ │  │
│  │  │   Payload: { context_id, model, temperature }       │ │  │
│  │  │   Response: { generated_text, model_used, ... }     │ │  │
│  │  │                                                      │ │  │
│  │  │ POST /api/ai-chat                                   │ │  │
│  │  │   Payload: { messages, model, system_prompt }       │ │  │
│  │  │   Response: { message, model_used, tokens_used }    │ │  │
│  │  │                                                      │ │  │
│  │  │ GET /api/models                                     │ │  │
│  │  │   Response: [{ id, name, provider, available }]     │ │  │
│  │  │                                                      │ │  │
│  │  │ GET /api/conversations/{id}                         │ │  │
│  │  │   Response: { id, messages[], created_at, ... }     │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Settings & Statistics Routes                         │ │  │
│  │  │                                                      │ │  │
│  │  │ GET  /api/settings                                  │ │  │
│  │  │ POST /api/settings                                  │ │  │
│  │  │   Payload: { theme, api_key, auto_save, ... }       │ │  │
│  │  │                                                      │ │  │
│  │  │ GET /api/stats                                      │ │  │
│  │  │   Response: { total_contexts, total_chats, ... }    │ │  │
│  │  │                                                      │ │  │
│  │  │ GET /health                                         │ │  │
│  │  │   Response: { status: "ok", uptime, version }       │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  SERVICE LAYER (Business Logic)                            │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ AI Service (ai_service.py)                           │ │  │
│  │  │                                                      │ │  │
│  │  │ - Model initialization & management                  │ │  │
│  │  │ - Prompt generation using local models               │ │  │
│  │  │ - Chat completion (OpenAI, Anthropic, Local)         │ │  │
│  │  │ - Embedding generation (Sentence Transformers)       │ │  │
│  │  │ - Token counting & estimation                        │ │  │
│  │  │ - Temperature & parameter tuning                     │ │  │
│  │  │ - Multi-model support with fallback logic            │ │  │
│  │  │ - Rate limiting & usage tracking                     │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Database Service (storage.py + db_storage.py)        │ │  │
│  │  │                                                      │ │  │
│  │  │ - Context CRUD operations                            │ │  │
│  │  │ - Search & filtering capabilities                    │ │  │
│  │  │ - Transaction management                             │ │  │
│  │  │ - Relationship handling (contexts ↔ messages)        │ │  │
│  │  │ - Connection pooling                                 │ │  │
│  │  │ - Data persistence & queries                         │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Caching Services                                     │ │  │
│  │  │                                                      │ │  │
│  │  │ Response Cache (response_cache.py)                   │ │  │
│  │  │  - Cache AI model outputs                            │ │  │
│  │  │  - TTL-based expiration                              │ │  │
│  │  │  - Cache hit/miss tracking                           │ │  │
│  │  │                                                      │ │  │
│  │  │ Embedding Cache (embedding_cache.py)                 │ │  │
│  │  │  - Store computed embeddings                         │ │  │
│  │  │  - Semantic search optimization                      │ │  │
│  │  │  - Fast retrieval without re-encoding                │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Utility Services                                     │ │  │
│  │  │                                                      │ │  │
│  │  │ Settings Store (settings_store.py)                   │ │  │
│  │  │  - User preferences (JSON file storage)              │ │  │
│  │  │  - Theme, API keys, auto-save settings               │ │  │
│  │  │                                                      │ │  │
│  │  │ Request Tracking (request_tracking.py)               │ │  │
│  │  │  - API usage monitoring                              │ │  │
│  │  │  - Request/response logging                          │ │  │
│  │  │  - Performance metrics                               │ │  │
│  │  │                                                      │ │  │
│  │  │ Relevance Scoring (relevance.py)                     │ │  │
│  │  │  - Search result ranking                             │ │  │
│  │  │  - Context similarity calculation                    │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DATA MODELS (models.py + db_models.py)                    │  │
│  │                                                            │  │
│  │  API Request/Response Models (Pydantic):                   │  │
│  │  - ContextCreate, ContextUpdate, ContextResponse            │  │
│  │  - MessageCreate, MessageResponse                           │  │
│  │  - ChatRequest, ChatResponse                                │  │
│  │  - SettingsRequest, SettingsResponse                        │  │
│  │  - StatsResponse                                            │  │
│  │  - ErrorResponse                                            │  │
│  │                                                            │  │
│  │  Database Models (SQLAlchemy ORM):                          │  │
│  │  - Context (id, title, content, metadata, created_at)       │  │
│  │  - Message (id, context_id, role, content, timestamp)       │  │
│  │  - Conversation (id, messages[], created_at)                │  │
│  │  - Relationship: Context → Messages (1:N)                   │  │
│  │  - Relationship: Context → Conversations (1:N)              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DEPENDENCIES & EXTERNAL INTEGRATIONS                       │  │
│  │                                                            │  │
│  │  FastAPI 0.109.0       - Web Framework                    │  │
│  │  Uvicorn 0.27.0        - ASGI Server                      │  │
│  │  Pydantic 2.5.3         - Data Validation                  │  │
│  │  SQLAlchemy 2.0.25      - ORM Layer                        │  │
│  │  Sentence-Transformers - Embeddings                       │  │
│  │  Torch 2.0.1            - Deep Learning                    │  │
│  │  Transformers 4.30.0    - NLP Models                       │  │
│  │  OpenAI API >= 1.52.0   - GPT Integration                  │  │
│  │  Anthropic >= 0.70.0    - Claude Integration               │  │
│  │  HuggingFace Hub        - Model Downloads                  │  │
│  │  Pytest >= 8.2          - Testing Framework                │  │
│  │  Alembic 1.13.1         - Database Migrations              │  │
│  │  SlowAPI 0.1.9          - Rate Limiting                    │  │
│  │  Python Multipart       - File Upload Support              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. DATABASE ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                  │
│              (SQLite + SQLAlchemy ORM)                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DATABASE CONFIGURATION (database.py)                      │  │
│  │                                                            │  │
│  │  - SQLite File: contextpilot.db (SQLite)                  │  │
│  │  - Connection String: sqlite:///contextpilot.db            │  │
│  │  - Connection Pool: NullPool (no pooling for SQLite)       │  │
│  │  - Echo: False (no SQL logging)                            │  │
│  │  - Thread Safety: Check same_thread=False                  │  │
│  │                                                            │  │
│  │  For Testing:                                              │  │
│  │  - In-Memory DB: sqlite:///:memory:                        │  │
│  │  - Per-Test Isolation: Monkeypatch fixtures                │  │
│  │  - Session Factory: TestSessionLocal                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  TABLES & SCHEMA                                           │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ TABLE: context                                       │ │  │
│  │  ├──────────────────────────────────────────────────────┤ │  │
│  │  │ Columns:                                             │ │  │
│  │  │  - id (Integer, PK)                                  │ │  │
│  │  │  - title (String, NOT NULL)                          │ │  │
│  │  │  - content (Text, NOT NULL)                          │ │  │
│  │  │  - metadata (JSON, nullable)                         │ │  │
│  │  │  - created_at (DateTime, default=now)                │ │  │
│  │  │  - updated_at (DateTime, onupdate=now)               │ │  │
│  │  │  - tags (String, comma-separated)                    │ │  │
│  │  │  - source (String, optional)                         │ │  │
│  │  │  - embedding (Vector, nullable)                      │ │  │
│  │  │                                                      │ │  │
│  │  │ Indexes:                                             │ │  │
│  │  │  - title (for search)                                │ │  │
│  │  │  - created_at (for sorting)                          │ │  │
│  │  │  - tags (for filtering)                              │ │  │
│  │  │                                                      │ │  │
│  │  │ Relationships:                                        │ │  │
│  │  │  - messages (1:N) → Message table                    │ │  │
│  │  │  - conversations (1:N) → Conversation table          │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ TABLE: message                                       │ │  │
│  │  ├──────────────────────────────────────────────────────┤ │  │
│  │  │ Columns:                                             │ │  │
│  │  │  - id (Integer, PK)                                  │ │  │
│  │  │  - context_id (Integer, FK → context.id)             │ │  │
│  │  │  - role (String, enum: user|assistant|system)        │ │  │
│  │  │  - content (Text)                                    │ │  │
│  │  │  - timestamp (DateTime)                              │ │  │
│  │  │  - metadata (JSON, optional)                         │ │  │
│  │  │  - model_used (String, optional)                     │ │  │
│  │  │  - tokens_used (Integer, optional)                   │ │  │
│  │  │                                                      │ │  │
│  │  │ Relationships:                                        │ │  │
│  │  │  - context (N:1) → Context                           │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ TABLE: conversation                                  │ │  │
│  │  ├──────────────────────────────────────────────────────┤ │  │
│  │  │ Columns:                                             │ │  │
│  │  │  - id (Integer, PK)                                  │ │  │
│  │  │  - context_id (Integer, FK → context.id)             │ │  │
│  │  │  - title (String, optional)                          │ │  │
│  │  │  - summary (Text, optional)                          │ │  │
│  │  │  - created_at (DateTime)                             │ │  │
│  │  │  - updated_at (DateTime)                             │ │  │
│  │  │  - message_count (Integer)                           │ │  │
│  │  │                                                      │ │  │
│  │  │ Relationships:                                        │ │  │
│  │  │  - context (N:1) → Context                           │ │  │
│  │  │  - messages (1:N) → Message table (via context)      │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  SQLAlchemy ORM MAPPING                                    │  │
│  │                                                            │  │
│  │  db_models.py provides:                                    │  │
│  │                                                            │  │
│  │  class Context(Base):                                      │  │
│  │    __tablename__ = "context"                               │  │
│  │    id, title, content, metadata, created_at, updated_at    │  │
│  │    messages = relationship("Message", back_populates=...)  │  │
│  │    conversations = relationship("Conversation", ...)       │  │
│  │                                                            │  │
│  │  class Message(Base):                                      │  │
│  │    __tablename__ = "message"                               │  │
│  │    id, context_id, role, content, timestamp, ...           │  │
│  │    context = relationship("Context", back_populates=...)   │  │
│  │                                                            │  │
│  │  class Conversation(Base):                                 │  │
│  │    __tablename__ = "conversation"                          │  │
│  │    id, context_id, title, summary, created_at, ...         │  │
│  │    context = relationship("Context", back_populates=...)   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DATABASE ACCESS PATTERNS                                  │  │
│  │                                                            │  │
│  │  Session Management:                                       │  │
│  │  - SessionLocal factory for creating DB sessions           │  │
│  │  - Context manager for automatic cleanup                   │  │
│  │  - Dependency injection via get_db_session()               │  │
│  │                                                            │  │
│  │  Common Queries:                                            │  │
│  │  - SELECT * FROM context WHERE title LIKE ?                │  │
│  │  - SELECT * FROM message WHERE context_id = ?              │  │
│  │  - JOIN context ON conversation.context_id = context.id    │  │
│  │  - ORDER BY context.created_at DESC LIMIT 10               │  │
│  │                                                            │  │
│  │  Transactions:                                              │  │
│  │  - Automatic transaction management via SQLAlchemy         │  │
│  │  - Rollback on exceptions                                  │ │  │
│  │  - Commit on successful operations                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  DATABASE MIGRATIONS (Alembic)                             │  │
│  │                                                            │  │
│  │  - Automatic schema versioning                             │  │
│  │  - alembic/versions/ directory contains migration scripts   │  │
│  │  - Commands:                                                │  │
│  │    * alembic init alembic         (initialize)              │  │
│  │    * alembic revision --autogenerate -m "message"           │  │
│  │    * alembic upgrade head         (apply migrations)        │  │
│  │    * alembic downgrade -1         (rollback)                │  │
│  │                                                            │  │
│  │ - Tracks database schema evolution over time                │  │
│  │ - Allows rollback to previous versions                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. AI SERVICES ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                    AI SERVICE LAYER                                │
│                    (ai_service.py)                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  AI SERVICE INITIALIZATION                                │  │
│  │                                                            │  │
│  │  - Lazy loading of models (on first use)                   │  │
│  │  - Environment variable configuration                      │  │
│  │  - Dependency injection for database access                │  │
│  │  - Error handling & fallback mechanisms                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │
│        ┌──────────────────┼──────────────────┬──────────────┐
│        │                  │                  │              │
│        ▼                  ▼                  ▼              ▼
│  ┌──────────┐    ┌──────────────┐   ┌──────────────┐  ┌────────┐
│  │  LOCAL   │    │  OPENAI API  │   │ ANTHROPIC API│  │ OLLAMA │
│  │  MODELS  │    │              │   │              │  │ LOCAL  │
│  └──────────┘    └──────────────┘   └──────────────┘  └────────┘
│        │                  │                  │              │
│        └──────────────────┼──────────────────┴──────────────┘
│                           │
│                    ┌──────▼──────┐
│                    │ AI SERVICE  │
│                    │ INTERFACE   │
│                    └─────────────┘
│
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LOCAL MODELS (Using Transformers/Torch)                   │  │
│  │                                                            │  │
│  │  - Model: distilbert-base-uncased                          │  │
│  │  - Purpose: Local text generation & analysis               │  │
│  │  - Framework: Hugging Face Transformers                    │  │
│  │  - GPU Support: CUDA/MPS if available                      │  │
│  │  - Advantages:                                             │  │
│  │    * No API costs                                          │  │
│  │    * Privacy-preserved (runs locally)                      │  │
│  │    * No rate limits                                        │  │
│  │    * Instant response                                      │  │
│  │  - Disadvantages:                                          │  │
│  │    * Lower quality than larger models                      │  │
│  │    * Slower than API-based models                          │  │
│  │    * Requires significant memory                           │  │
│  │                                                            │  │
│  │  Functions:                                                │  │
│  │  - generate_text(prompt, max_length)                       │  │
│  │  - generate_embedding(text)                                │  │
│  │  - count_tokens(text)                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  OPENAI INTEGRATION (GPT-3.5, GPT-4)                        │  │
│  │                                                            │  │
│  │  Configuration:                                            │  │
│  │  - API Key: OPENAI_API_KEY environment variable            │  │
│  │  - Models: gpt-3.5-turbo, gpt-4, gpt-4-turbo               │  │
│  │  - Base URL: https://api.openai.com/v1 (or custom proxy)   │  │
│  │                                                            │  │
│  │  Functions:                                                │  │
│  │  - chat_completion(messages, model, temperature)           │  │
│  │    * system, user, assistant roles                         │  │
│  │    * temperature for creativity (0-2)                      │  │
│  │    * max_tokens limiting                                   │  │
│  │    * Response caching via response_cache.py                │  │
│  │                                                            │  │
│  │  - count_tokens(text)                                      │  │
│  │    * Token counting for billing & limits                   │  │
│  │                                                            │  │
│  │  Error Handling:                                            │  │
│  │  - API rate limiting (429)                                 │  │
│  │  - Timeout errors (fallback to local)                      │  │
│  │  - Invalid API key (clear error message)                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ANTHROPIC INTEGRATION (Claude Models)                      │  │
│  │                                                            │  │
│  │  Configuration:                                            │  │
│  │  - API Key: ANTHROPIC_API_KEY environment variable         │  │
│  │  - Models: claude-3-opus, claude-3-sonnet, claude-3-haiku   │  │
│  │  - Base URL: https://api.anthropic.com                     │  │
│  │                                                            │  │
│  │  Functions:                                                │  │
│  │  - chat_completion(messages, model, temperature)           │  │
│  │    * Enhanced context understanding                        │  │
│  │    * Better reasoning capabilities                         │  │
│  │    * System prompt support                                 │  │
│  │                                                            │  │
│  │  Error Handling:                                            │  │
│  │  - API availability checks                                 │  │
│  │  - Graceful fallback to OpenAI/local                       │  │
│  │  - Timeout handling                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  OLLAMA LOCAL INFERENCE                                    │  │
│  │                                                            │  │
│  │  Configuration:                                            │  │
│  │  - Base URL: http://localhost:11434                        │  │
│  │  - Models: llama2, mistral, neural-chat, etc. (auto-pull)   │  │
│  │                                                            │  │
│  │  Functions:                                                │  │
│  │  - generate(model, prompt, temperature)                    │  │
│  │  - chat(model, messages)                                   │  │
│  │  - list_models()                                           │  │
│  │                                                            │  │
│  │  Advantages:                                                │  │
│  │  - Completely private (no API calls)                       │  │
│  │  - Free to use                                             │  │
│  │  - Fast local inference                                    │  │
│  │  - Supports custom model selection                         │  │
│  │  - Automatic model downloading                             │  │
│  │                                                            │  │
│  │  Disadvantages:                                             │  │
│  │  - Requires Ollama installation                            │  │
│  │  - Slower than API-based models                            │  │
│  │  - Limited to system resources                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  EMBEDDING SERVICE                                         │  │
│  │                                                            │  │
│  │  Sentence Transformers (sentence-transformers 2.2.2)       │  │
│  │  - Model: all-MiniLM-L6-v2                                 │  │
│  │  - Purpose: Semantic search & similarity                   │  │
│  │  - Dimension: 384D vectors                                 │  │
│  │  - Speed: Fast on CPU/GPU                                  │  │
│  │                                                            │  │
│  │  Functions:                                                │  │
│  │  - embed_text(text)                                        │  │
│  │    * Input: Text string                                    │  │
│  │    * Output: 384D numpy array                              │  │
│  │    * Cache: Via embedding_cache.py                         │  │
│  │                                                            │  │
│  │  - semantic_search(query, contexts)                        │  │
│  │    * Rank contexts by relevance to query                   │  │
│  │    * Uses cosine similarity                                │  │
│  │    * Returns ranked results                                │  │
│  │                                                            │  │
│  │  - similarity_score(text1, text2)                          │  │
│  │    * Cosine similarity between 0-1                         │  │
│  │    * Cached for efficiency                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  MODEL SELECTION STRATEGY                                  │  │
│  │                                                            │  │
│  │  Priority Order:                                            │  │
│  │  1. User-selected model (from settings)                    │  │
│  │  2. OpenAI (if API key configured)                         │  │
│  │  3. Anthropic (if API key configured)                      │  │
│  │  4. Ollama (if running locally)                            │  │
│  │  5. Local models (always available)                        │  │
│  │                                                            │  │
│  │  Fallback Mechanism:                                        │  │
│  │  - If selected model fails → try next in priority          │  │
│  │  - If all external APIs fail → use local model             │  │
│  │  - User notified of model change via response               │  │
│  │  - Logging tracks all fallbacks                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  CACHING LAYER                                             │  │
│  │                                                            │  │
│  │  Response Cache (response_cache.py)                        │  │
│  │  - Cache key: hash(model + prompt + params)                │  │
│  │  - TTL: Configurable (default 1 hour)                      │  │
│  │  - Storage: In-memory dict + optional disk persistence     │  │
│  │  - Hit rate tracking                                       │  │
│  │                                                            │  │
│  │  Embedding Cache (embedding_cache.py)                      │  │
│  │  - Cache key: hash(text)                                   │  │
│  │  - No expiration (embeddings stable)                       │  │
│  │  - Persistent storage to avoid recomputation               │  │
│  │  - Significant speedup for repeated texts                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. BUILD & DEPLOYMENT ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                  BUILD & DEPLOYMENT SYSTEM                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FRONTEND BUILD PIPELINE                                   │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Development Build (npm run dev)                      │ │  │
│  │  │                                                      │ │  │
│  │  │  1. Vite Dev Server Start                            │ │  │
│  │  │     - Listen on localhost:5173                       │ │  │
│  │  │     - Configure proxy to /api → localhost:8000       │ │  │
│  │  │     - Enable Hot Module Replacement (HMR)            │ │  │
│  │  │                                                      │ │  │
│  │  │  2. File Watching                                    │ │  │
│  │  │     - Watch src/*.tsx, src/*.ts, index.html          │ │  │
│  │  │     - Reload on changes                              │ │  │
│  │  │     - Preserve app state via HMR                     │ │  │
│  │  │                                                      │ │  │
│  │  │  3. Asset Processing                                 │ │  │
│  │  │     - TypeScript → JavaScript (esbuild)              │ │  │
│  │  │     - JSX → React calls                              │ │  │
│  │  │     - CSS bundling & scoping                         │ │  │
│  │  │                                                      │ │  │
│  │  │  4. Development Features                             │ │  │
│  │  │     - Source maps for debugging                      │ │  │
│  │  │     - No minification (faster builds)                │ │  │
│  │  │     - CORS enabled for API calls                     │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Production Build (npm run build)                     │ │  │
│  │  │                                                      │ │  │
│  │  │  1. TypeScript Type Checking                         │ │  │
│  │  │     - Validate types before bundling                 │ │  │
│  │  │     - Strict mode enabled                            │ │  │
│  │  │                                                      │ │  │
│  │  │  2. Bundling & Optimization                          │ │  │
│  │  │     - Minify JS/CSS (esbuild)                        │ │  │
│  │  │     - Tree-shake unused code                         │ │  │
│  │  │     - Split chunks for caching                       │ │  │
│  │  │     - Chunk size warning limit: 800KB                │ │  │
│  │  │                                                      │ │  │
│  │  │  3. Asset Processing                                 │ │  │
│  │  │     - Compress images                                │ │  │
│  │  │     - Hash filenames for cache busting               │ │  │
│  │  │     - Inline small assets                            │ │  │
│  │  │                                                      │ │  │
│  │  │  4. Output                                            │ │  │
│  │  │     - Output directory: dist/                        │ │  │
│  │  │     - index.html (entry point)                       │ │  │
│  │  │     - assets/ (JS, CSS, images)                      │ │  │
│  │  │     - Ready for static hosting                       │ │  │
│  │  │                                                      │ │  │
│  │  │  5. Build Analysis                                    │ │  │
│  │  │     - Bundle size reporting                          │ │  │
│  │  │     - Performance insights                           │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  BACKEND BUILD & RUN                                       │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Development Run (python main.py)                     │ │  │
│  │  │                                                      │ │  │
│  │  │  1. Virtual Environment                              │ │  │
│  │  │     - source venv/bin/activate                       │ │  │
│  │  │     - Python 3.9.6 from venv                         │ │  │
│  │  │     - Isolated dependencies                          │ │  │
│  │  │                                                      │ │  │
│  │  │  2. Dependency Loading                               │ │  │
│  │  │     - Import FastAPI, SQLAlchemy, AI services        │ │  │
│  │  │     - Initialize database connection                 │ │  │
│  │  │     - Load environment variables (.env)              │ │  │
│  │  │                                                      │ │  │
│  │  │  3. Server Start                                      │ │  │
│  │  │     - Uvicorn ASGI server                            │ │  │
│  │  │     - Listen on 0.0.0.0:8000                         │ │  │
│  │  │     - Reload on file changes (debug mode)            │ │  │
│  │  │     - All routes registered                          │ │  │
│  │  │                                                      │ │  │
│  │  │  4. Logging & Monitoring                              │ │  │
│  │  │     - Request logging to stdout/backend.log          │ │  │
│  │  │     - Error logging & stack traces                   │ │  │
│  │  │     - Request tracking enabled                       │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Testing (pytest)                                     │ │  │
│  │  │                                                      │ │  │
│  │  │  1. Test Configuration (conftest.py)                 │ │  │
│  │  │     - Force in-memory storage for unit tests         │ │  │
│  │  │     - Create per-test database (db_store fixture)    │ │  │
│  │  │     - Monkeypatch for dependency injection           │ │  │
│  │  │     - Suppress warnings (LibreSSL, urllib3)          │ │  │
│  │  │                                                      │ │  │
│  │  │  2. Test Types                                        │ │  │
│  │  │     - Unit: test_*.py (isolated function tests)      │ │  │
│  │  │     - Integration: test_integration.py (API routes)  │ │  │
│  │  │     - Database: test_db_*.py (ORM operations)        │ │  │
│  │  │     - Services: test_ai_service.py (AI logic)        │ │  │
│  │  │                                                      │ │  │
│  │  │  3. Test Runner                                       │ │  │
│  │  │     - pytest --tb=line -q                            │ │  │
│  │  │     - 183 tests total                                │ │  │
│  │  │     - All passing ✅                                 │ │  │
│  │  │     - Runtime: ~4.8 seconds                          │ │  │
│  │  │                                                      │ │  │
│  │  │  4. Coverage Reporting                                │ │  │
│  │  │     - pytest --cov for coverage analysis             │ │  │
│  │  │     - Identify untested code paths                   │ │  │
│  │  │     - Coverage requirements (if enforced)            │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ Database Migrations (Alembic)                        │ │  │
│  │  │                                                      │ │  │
│  │  │  1. Auto-generation                                  │ │  │
│  │  │     - alembic revision --autogenerate -m "name"      │ │  │
│  │  │     - Detects schema changes                         │ │  │
│  │  │     - Creates migration script                       │ │  │
│  │  │                                                      │ │  │
│  │  │  2. Application                                       │ │  │
│  │  │     - alembic upgrade head                           │ │  │
│  │  │     - Applies all pending migrations                 │ │  │
│  │  │     - Updates database schema                        │ │  │
│  │  │                                                      │ │  │
│  │  │  3. Rollback                                          │ │  │
│  │  │     - alembic downgrade -1                           │ │  │
│  │  │     - Reverts last migration                         │ │  │
│  │  │     - Restores previous schema                       │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  STARTUP SCRIPTS                                           │  │
│  │                                                            │  │
│  │  start.sh (Main Startup)                                   │  │
│  │  ├── setup.sh            (Initial setup)                   │  │
│  │  ├── start-backend.sh    (Backend server)                  │  │
│  │  └── start-frontend.sh   (Frontend dev server)             │  │
│  │                                                            │  │
│  │  setup.sh (One-time Setup)                                 │  │
│  │  ├── Create Python venv                                    │  │
│  │  ├── Install Python dependencies (pip install -r ...)     │  │
│  │  ├── Initialize database (python init_db.py)              │  │
│  │  ├── Install Node dependencies (npm install)              │  │
│  │  └── Test configuration (verify .env files)               │  │
│  │                                                            │  │
│  │  start-backend.sh (Backend)                                │  │
│  │  ├── Activate venv                                         │  │
│  │  ├── Set PYTHONPATH                                        │  │
│  │  ├── Export environment variables                          │  │
│  │  └── Run: python main.py                                   │  │
│  │                                                            │  │
│  │  start-frontend.sh (Frontend)                              │  │
│  │  ├── Navigate to frontend/                                 │  │
│  │  ├── Run: npm run dev                                      │  │
│  │  └── Open browser on localhost:5173                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ENVIRONMENT CONFIGURATION                                 │  │
│  │                                                            │  │
│  │  .env (Backend Configuration)                              │  │
│  │  ├── OPENAI_API_KEY=sk-...                                │ │  │
│  │  ├── ANTHROPIC_API_KEY=sk-ant-...                         │  │
│  │  ├── OLLAMA_BASE_URL=http://localhost:11434               │ │  │
│  │  ├── DATABASE_URL=sqlite:///contextpilot.db               │ │  │
│  │  ├── PYTHONPATH=/path/to/backend                          │ │  │
│  │  ├── CONTEXTPILOT_USE_DATABASE=true                       │ │  │
│  │  └── LOG_LEVEL=INFO                                        │ │  │
│  │                                                            │  │
│  │  .env.example (Template)                                   │  │
│  │  ├── Documents all environment variables                   │  │
│  │  ├── Default/example values provided                       │  │
│  │  └── User must copy to .env and configure                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 7. SECURITY & MIDDLEWARE ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│              SECURITY & MIDDLEWARE LAYER                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  SECURITY MEASURES (security.py)                           │  │
│  │                                                            │  │
│  │  API Key Protection:                                        │  │
│  │  - OpenAI/Anthropic keys never logged                      │  │
│  │  - Keys stored in .env (not committed to git)              │  │
│  │  - Environment-based configuration                         │  │
│  │                                                            │  │
│  │  Input Validation:                                          │  │
│  │  - Pydantic models validate all inputs                     │  │
│  │  - Type checking & constraints                             │  │
│  │  - SQL injection prevention (ORM parameterization)         │  │
│  │  - XSS prevention (content sanitization)                   │  │
│  │                                                            │  │
│  │  Error Handling:                                            │  │
│  │  - Generic error responses to clients                      │  │
│  │  - Detailed logging for debugging                          │  │
│  │  - No stack traces exposed to users                        │  │
│  │  - Graceful fallback mechanisms                            │  │
│  │                                                            │  │
│  │  HTTPS/TLS:                                                 │  │
│  │  - Dev: Plain HTTP on localhost (safe)                     │  │
│  │  - Prod: HTTPS enforced via reverse proxy/nginx            │  │
│  │  - HSTS headers recommended                                │  │
│  │  - SSL certificate management (Let's Encrypt)              │  │
│  │                                                            │  │
│  │  Rate Limiting (SlowAPI):                                   │  │
│  │  - Limit requests per IP                                   │  │
│  │  - Prevent brute force attacks                             │  │
│  │  - Protect expensive endpoints (/ai-chat, /generate)       │  │
│  │  - Configurable limits per route                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  MIDDLEWARE STACK (in main.py)                             │  │
│  │                                                            │  │
│  │  Request Flow:                                              │  │
│  │                                                            │  │
│  │  1. HTTP Request                                            │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  2. CORS Middleware                                        │  │
│  │     - Allow frontend requests (localhost:5173/3000)        │  │
│  │     - Whitelist allowed origins                            │  │
│  │     - Allow credentials if needed                          │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  3. Request Tracking Middleware                            │  │
│  │     - Log request ID, method, path                         │  │
│  │     - Track start time                                     │  │
│  │     - Record user agent, IP                                │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  4. Rate Limiting Middleware                               │  │
│  │     - Check request rate per IP                            │  │
│  │     - Return 429 if limit exceeded                         │  │
│  │     - Add rate limit headers                               │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  5. Security Headers Middleware                            │  │
│  │     - X-Content-Type-Options: nosniff                      │  │
│  │     - X-Frame-Options: DENY                                │  │
│  │     - X-XSS-Protection header                              │  │
│  │     - Content-Security-Policy                              │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  6. Route Handler                                           │  │
│  │     - Input validation (Pydantic)                          │  │
│  │     - Dependency injection (database session)              │  │
│  │     - Business logic execution                             │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  7. Response Processing                                    │  │
│  │     - Serialize response to JSON                           │  │
│  │     - Log response status & time                           │  │
│  │     - Set response headers                                 │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  8. HTTP Response                                           │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  ERROR HANDLING                                            │  │
│  │                                                            │  │
│  │  Exception Types:                                           │  │
│  │  - HTTPException: Explicit API errors                      │  │
│  │  - ValidationError: Pydantic validation failures           │  │
│  │  - DatabaseError: Database operation failures              │  │
│  │  - APIError: External API integration failures             │  │
│  │                                                            │  │
│  │  Error Response Format:                                     │  │
│  │  {                                                          │  │
│  │    "detail": "Human-readable error message",               │  │
│  │    "status_code": 400|404|500,                             │  │
│  │    "timestamp": "2026-02-05T12:00:00Z",                    │  │
│  │    "request_id": "uuid"                                    │  │
│  │  }                                                          │  │
│  │                                                            │  │
│  │  Status Codes:                                              │  │
│  │  - 200: Success                                            │  │
│  │  - 201: Created                                            │  │
│  │  - 400: Bad Request (validation error)                     │  │
│  │  - 404: Not Found                                          │  │
│  │  - 429: Too Many Requests (rate limit)                     │  │
│  │  - 500: Internal Server Error                              │  │
│  │  - 503: Service Unavailable (AI API down)                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  LOGGING ARCHITECTURE                                      │  │
│  │                                                            │  │
│  │  Logger Configuration (logger.py):                          │  │
│  │  - Format: timestamp | level | module | message            │  │
│  │  - Level: DEBUG < INFO < WARNING < ERROR < CRITICAL        │  │
│  │  - Outputs: stdout + backend.log file                      │  │
│  │                                                            │  │
│  │  Log Channels:                                              │  │
│  │  - API Access: All HTTP requests/responses                 │  │
│  │  - Business Logic: AI service operations                   │  │
│  │  - Database: ORM operations & queries                      │  │
│  │  - Security: Auth failures, rate limit hits                │  │
│  │  - Performance: Slow queries, timeouts                     │  │
│  │  - Errors: Exceptions & stack traces                       │  │
│  │                                                            │  │
│  │  Log Retention:                                             │  │
│  │  - Daily rotation (if size-based rotation configured)      │  │
│  │  - 7-day retention (configurable)                          │  │
│  │  - Cleanup of old logs automated                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 8. DATA FLOW DIAGRAMS

### Context Creation Flow

```
User Input (Frontend)
    │
    ├─ Title, Content, Tags
    │
    ▼
API Call: POST /api/contexts
    │
    ├─ Validation (Pydantic)
    ├─ Security checks
    │
    ▼
Create Handler (routes)
    │
    ├─ Generate embedding (ai_service.generate_embedding)
    ├─ Validate content
    │
    ▼
Database Layer (db_storage.create_context)
    │
    ├─ Create Context record
    ├─ Store in SQLite
    ├─ Return ID
    │
    ▼
Cache Layer
    │
    ├─ Store embedding (embedding_cache)
    │
    ▼
Response to Frontend
    │
    ├─ ID, created_at, title
    │
    ▼
UI Update
    ├─ Add to context list
    ├─ Show success message
```

### AI Chat Flow

```
User Message (Frontend)
    │
    ├─ Context ID, message text
    │
    ▼
API Call: POST /api/ai-chat
    │
    ├─ Validation
    ├─ Check rate limits (SlowAPI)
    │
    ▼
Chat Handler (routes)
    │
    ├─ Load conversation history
    ├─ Build prompt with context
    │
    ▼
Response Cache Check (response_cache)
    │
    ├─ Cache hit? → Return cached response
    ├─ Cache miss? → Continue
    │
    ▼
AI Service (ai_service)
    │
    ├─ Select model (priority: user choice → OpenAI → Anthropic → Local)
    ├─ Call API or local inference
    ├─ Handle streaming (if supported)
    ├─ Count tokens
    │
    ▼
Error Handling / Fallback
    │
    ├─ API error? → Try next model
    ├─ All APIs down? → Use local model
    │
    ▼
Store Response
    │
    ├─ Save to database (Message record)
    ├─ Cache response
    ├─ Update conversation
    │
    ▼
Response to Frontend
    │
    ├─ Message content
    ├─ Model used
    ├─ Tokens consumed
    │
    ▼
UI Update
    ├─ Display message
    ├─ Show model info
    ├─ Update token count
```

### Search & Retrieval Flow

```
Search Query (Frontend)
    │
    ├─ Search term
    │
    ▼
API Call: GET /api/contexts?search=term
    │
    ├─ Validation
    │
    ▼
Search Handler (routes)
    │
    ├─ Embedding query text
    ├─ Vector similarity search
    │
    ▼
Database Query
    │
    ├─ Full-text search on title/content
    ├─ Semantic search using embeddings
    ├─ Combine results (rank by relevance)
    │
    ▼
Relevance Scoring (relevance.py)
    │
    ├─ BM25 score for text match
    ├─ Cosine similarity for embeddings
    ├─ Combined ranking
    │
    ▼
Result Processing
    │
    ├─ Paginate (limit, offset)
    ├─ Format response
    │
    ▼
Response to Frontend
    │
    ├─ Ranked context list
    ├─ Match scores
    │
    ▼
UI Update
    ├─ Display results
    ├─ Highlight matches
```

---

## 9. TECHNOLOGY STACK SUMMARY

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend Build** | Vite | 7.3.1 | Fast build tool & dev server |
| **Frontend Framework** | React | 18.3.1 | UI library |
| **Language** | TypeScript | 4.9.5 | Type-safe JavaScript |
| **HTTP Client** | Axios | 1.13.4 | API requests |
| **Markdown** | React-Markdown | 10.1.0 | Render markdown content |
| **Code Highlight** | Highlight.js | 11.11.1 | Syntax highlighting |
| | Rehype-Highlight | 7.0.2 | Integration plugin |
| | Remark GFM | 4.0.1 | GitHub flavored markdown |
| **Backend Framework** | FastAPI | 0.109.0 | Modern async web framework |
| **ASGI Server** | Uvicorn | 0.27.0 | Production server |
| **Data Validation** | Pydantic | 2.5.3 | Input/output validation |
| **Database ORM** | SQLAlchemy | 2.0.25 | Object-relational mapping |
| **Database** | SQLite | - | Embedded database |
| **Migrations** | Alembic | 1.13.1 | Schema versioning |
| **Machine Learning** | PyTorch | 2.0.1 | Deep learning framework |
| **NLP** | Transformers | 4.30.0 | Pre-trained models |
| **Embeddings** | Sentence-Transformers | 2.2.2 | Text embedding models |
| **Rate Limiting** | SlowAPI | 0.1.9 | API rate limiting |
| **Testing** | Pytest | 8.4.2 | Test framework |
| **External APIs** | OpenAI | >=1.52.0 | GPT integration |
| | Anthropic | >=0.70.0 | Claude integration |
| **Local LLM** | Ollama | - | Local inference |

---

## 10. DEPLOYMENT CONSIDERATIONS

```
┌─────────────────────────────────────────────────────────────┐
│               DEPLOYMENT ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Development (Current Setup):                               │
│  ├─ Frontend: localhost:5173 (Vite Dev Server)             │
│  ├─ Backend: localhost:8000 (Python Uvicorn)              │
│  ├─ Database: SQLite (contextpilot.db)                    │
│  ├─ Proxy: Vite proxies /api → backend                    │
│  └─ CORS: Enabled for localhost                            │
│                                                             │
│  Production (Recommended):                                  │
│  ├─ Frontend:                                               │
│  │  ├─ Build: npm run build → dist/                       │
│  │  ├─ Hosting: S3/CloudFront, Vercel, or Netlify         │
│  │  ├─ CDN: Global content distribution                    │
│  │  └─ HTTPS: Enabled via CloudFront/CDN                  │
│  │                                                         │
│  ├─ Backend:                                                │
│  │  ├─ Container: Docker (recommended)                     │
│  │  ├─ Orchestration: Kubernetes or Docker Compose        │
│  │  ├─ Server: Gunicorn/Uvicorn with multiple workers     │
│  │  ├─ Reverse Proxy: Nginx with SSL/TLS                  │
│  │  ├─ Load Balancing: Multiple backend instances         │
│  │  └─ HTTPS: SSL termination at Nginx                    │
│  │                                                         │
│  ├─ Database:                                               │
│  │  ├─ PostgreSQL recommended (not SQLite)                 │
│  │  ├─ Connection pooling (pgBouncer)                      │
│  │  ├─ Backup strategy: Daily automated backups            │
│  │  ├─ Replication: Hot standby for high availability      │
│  │  └─ Monitoring: Query performance, disk space           │
│  │                                                         │
│  ├─ Infrastructure:                                         │
│  │  ├─ Cloud: AWS, GCP, Azure, or DigitalOcean            │
│  │  ├─ CI/CD: GitHub Actions, GitLab CI, or Jenkins       │
│  │  ├─ Monitoring: Prometheus, Datadog, or New Relic       │
│  │  ├─ Logging: ELK Stack, Splunk, or CloudWatch          │
│  │  ├─ Caching: Redis for response & session caching      │
│  │  └─ Secrets: Vault or AWS Secrets Manager              │
│  │                                                         │
│  └─ Scaling:                                                │
│     ├─ Horizontal: Load-balanced backend instances         │
│     ├─ Vertical: Larger compute instances                  │
│     ├─ Database: Read replicas for queries                 │
│     ├─ Caching: Redis for faster responses                 │
│     └─ CDN: Global edge locations for frontend             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. KEY ARCHITECTURAL PRINCIPLES

1. **Separation of Concerns**: Frontend, Backend, Database, and AI Services are independent layers
2. **Dependency Injection**: Services receive dependencies rather than creating them
3. **Async/Await**: FastAPI uses async handlers for non-blocking I/O
4. **ORM Pattern**: SQLAlchemy abstracts database details
5. **Caching Strategy**: Multi-level caching (responses, embeddings) for performance
6. **Fallback Mechanism**: Multiple AI providers with intelligent failover
7. **Type Safety**: TypeScript frontend + Pydantic backend validation
8. **Testing**: Unit, integration, and functional test coverage
9. **Error Handling**: Graceful degradation and user-friendly error messages
10. **Security**: Input validation, API key protection, CORS, rate limiting

This architecture supports the application's core functionality while maintaining scalability, maintainability, and reliability.

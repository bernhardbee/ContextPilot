# Changelog

All notable changes to ContextPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Dynamic Model Discovery System**: Revolutionary auto-discovery of available AI models
  - **OpenAI Model API Discovery**: Fetches real-time available models from OpenAI API
  - **Anthropic Model Maintenance**: Curated list of current Anthropic models
  - **Ollama Auto-Detection**: Automatically discovers locally installed Ollama models
  - **24-Hour Intelligent Caching**: Optimized performance with smart cache management
  - **Robust Fallbacks**: System works even when APIs are unavailable
  - **Startup Integration**: Automatically refreshes model lists when backend starts
  - **Manual Discovery Tools**: Scripts for on-demand model refresh and testing
  - **JSON Configuration**: Dynamic model lists stored in `model_options.json` and `valid_models.json`
  - **Frontend Integration**: UI dynamically loads available models instead of hardcoded lists
  - **Backend Validation**: Server validates requests against actual available models
  - **Model Status Demo**: Built-in demo script to show current model availability
- **Ollama Integration**: Local AI model support using Ollama
  - Support for Llama 3.2, Llama 3.1, Mistral, CodeLlama, Phi-3, and more
  - OpenAI-compatible API integration (no new dependencies)
  - **Automatic Model Download**: Models are pulled automatically on first use
  - Privacy-first: all processing happens locally
  - No API costs or rate limits
  - Works offline
  - Configurable base URL (default: http://localhost:11434)
- **Provider Selection**: Added "Ollama (Local)" option in provider dropdown
- **Local Model List**: Model selector for Ollama models in chat interface and settings
- **Ollama Settings UI**: Configuration for Ollama base URL in settings modal
- **Ollama Tests**: Comprehensive test suite (12 tests) for Ollama integration
- **Model Attribution & Tracking**: Messages now show which AI model generated each response
  - Model information displayed in chat UI for transparency
  - Model tracking stored in database for each assistant message
  - Database migration script for existing installations
  - Per-message model history preserved in conversation data
  - UI styling for model badges in message bubbles
- **Full Markdown Rendering**: Complete markdown support using react-markdown
  - Syntax-highlighted code blocks with GitHub Dark theme
  - Inline code with custom styling
  - Bold, italic, strikethrough text formatting
  - Links (open in new tab with security attributes)
  - Lists (ordered and unordered)
  - Tables (via remark-gfm)
  - Blockquotes and headings
- **Code Syntax Highlighting**: Automatic language detection and highlighting via highlight.js
- **Markdown Image Support**: Chat interface now renders images from `![alt](url)` syntax automatically
- **Image Error Handling**: Failed image loads show helpful yellow warning boxes with links
- **Settings Auto-Loading**: Chat interface loads max_tokens and temperature from backend settings
- **Max Tokens Control**: Added visible max tokens input in chat interface (100-16000 range)
- **Immediate Message Display**: User messages appear instantly before API response
- **Concurrent Request Prevention**: Send button disabled during API calls to prevent multiple requests
- **Smart Truncation Handling**: Shows detailed messages for truncated responses with token counts
- **Input Auto-Clear**: Text box automatically clears on message send
- **Flexible Token Limits**: Supports up to 16,000 tokens (increased from 4,000)
- **Database Backup Scripts**: 
  - `backup_db.sh`: Creates timestamped backups, keeps last 10
  - `restore_db.sh`: Interactive restore with safety confirmations
  - `update_default_tokens.py`: Script to update legacy token limit settings
- **Enhanced Error Messages**: Empty response handling with finish_reason metadata
- **Comprehensive Logging**: Added debug logging throughout message lifecycle

### Changed
- **AI Provider Support**: Extended from 2 to 3 providers (OpenAI, Anthropic, Ollama)
- **Configuration**: Updated config.py, models.py, and main.py for Ollama support
- **AI Service**: Added Ollama client initialization and _generate_ollama() method
- **Settings API**: Extended to include ollama_configured and ollama_base_url fields
- **Frontend Types**: Updated Settings and SettingsUpdate interfaces for Ollama
- **Documentation**: Updated README.md and AI_INTEGRATION.md with Ollama setup instructions
- **Message Rendering**: Replaced custom parsing with ReactMarkdown for robust formatting
- **Max Tokens Default**: Increased from 2,000 to 4,000 tokens
- **Max Tokens Validation**: Increased limit from 4,000 to 16,000 tokens
- **Frontend Max Tokens UI**: Updated slider range to 16,000
- **Settings Loading**: Frontend now applies backend settings on load
- **Temperature Default**: Updated from 0.7 to 1.0 (correct default)
- **Test Coverage**: Improved to 135+ passing unit tests (now 147+ with Ollama tests)
- **API Response Handling**: Better null/empty content handling from OpenAI API

### Fixed
- **Console Logging**: Changed excessive warning logs to informational logs
- **Settings Application**: Frontend now loads and uses backend settings for chat
- **Low Token Limit Issue**: Fixed legacy 2000 token limit causing image truncation
- **AI Service Tests**: Fixed OpenAI SDK mocking to work with new SDK structure
- **Settings Validation Tests**: Updated to reflect new max_tokens limits
- **Empty Message Content**: Added safeguard for None responses from AI APIs
- **Message Rendering**: Fixed renderMessageContent to accept full message object with metadata
- **Truncated Responses**: Now properly detected and displayed with helpful messages
- **Code Block Display**: Code examples now render with proper formatting and highlighting

### Documentation
- **README.md**: 
  - Added Configuration section with settings management details
  - Added Database Backup & Restore section
  - Updated Chat & Conversations features list
  - Added image display documentation
  - Updated testing section with pytest commands
- **QUICKSTART.md**: 
  - Added backup/restore commands
  - Added conversation API endpoints
  - Updated test commands
- **AI_INTEGRATION.md**: 
  - Updated token limits (1-16000)
  - Updated default values
  - Added notes about preventing truncation
- **TESTING.md**: 
  - Updated test count (135+ passing)
  - Added AI service test coverage details
  - Added database session management tests
- **backend/README.md**: 
  - Added database management section
  - Updated features list
  - Added new test suites

### Technical
- Backend properly handles `None` content from OpenAI API with `or ""` fallback
- Frontend `renderMessageContent` now receives full `ConversationMessage` object
- Message metadata (tokens, finish_reason) used for better UX
- Improved error boundaries around image loading
- Enhanced console logging for debugging

## [Previous Versions]

### Chat & Conversation Features (Previous Release)
- Chat-style interface with message bubbles
- Conversation history with automatic persistence
- Smart context management (one-time sending per conversation)
- Auto-scroll to latest messages
- Context refresh control
- New conversation button

### Core Features (v1.0)
- CRUD operations for context units
- Persistent storage with SQLite/PostgreSQL
- AI integration with OpenAI and Anthropic
- Semantic search using sentence-transformers
- Embedding and response caching
- Context versioning and confidence scoring
- RESTful API with FastAPI
- React TypeScript frontend
- Settings management UI
- Context import/export (JSON/CSV)
- Security features (API key auth, validation, CORS, rate limiting)

# Changelog

All notable changes to ContextPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Markdown Image Support**: Chat interface now renders images from `![alt](url)` syntax automatically
- **Image Error Handling**: Failed image loads show helpful yellow warning boxes with links
- **Immediate Message Display**: User messages appear instantly before API response
- **Concurrent Request Prevention**: Send button disabled during API calls to prevent multiple requests
- **Smart Truncation Handling**: Shows detailed messages for truncated responses with token counts
- **Input Auto-Clear**: Text box automatically clears on message send
- **Flexible Token Limits**: Supports up to 16,000 tokens (increased from 4,000)
- **Database Backup Scripts**: 
  - `backup_db.sh`: Creates timestamped backups, keeps last 10
  - `restore_db.sh`: Interactive restore with safety confirmations
- **Enhanced Error Messages**: Empty response handling with finish_reason metadata
- **Comprehensive Logging**: Added debug logging throughout message lifecycle

### Changed
- **Max Tokens Default**: Increased from 2,000 to 4,000 tokens
- **Max Tokens Validation**: Increased limit from 4,000 to 16,000 tokens
- **Frontend Max Tokens UI**: Updated slider range to 16,000
- **Test Coverage**: Improved to 135+ passing unit tests
- **API Response Handling**: Better null/empty content handling from OpenAI API

### Fixed
- **AI Service Tests**: Fixed OpenAI SDK mocking to work with new SDK structure
- **Settings Validation Tests**: Updated to reflect new max_tokens limits
- **Empty Message Content**: Added safeguard for None responses from AI APIs
- **Message Rendering**: Fixed renderMessageContent to accept full message object with metadata
- **Truncated Responses**: Now properly detected and displayed with helpful messages

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

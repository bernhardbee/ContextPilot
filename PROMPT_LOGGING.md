# Prompt Logging & Traceability

ContextPilot includes comprehensive logging of all AI prompt generations to ensure full traceability and auditability of AI operations.

## Overview

Every time a prompt is generated (via `/generate-prompt` or `/generate-prompt/compact`), a detailed log entry is automatically created containing:

- **Unique Log ID**: Sequential identifier for tracking
- **Timestamp**: Exact time of generation (UTC)
- **Task**: The user's task/request
- **Contexts Used**: IDs and details of all context units used
- **Generated Prompt**: The complete prompt sent to the AI
- **Metadata**: Prompt type (full/compact), lengths, context types, etc.

## Features

### Automatic Logging
All prompt generations are automatically logged with no additional configuration required. Logs are stored in memory with a configurable maximum size (default: 10,000 entries).

### Complete Audit Trail
Each log entry captures:
```json
{
  "log_id": "prompt-000001",
  "timestamp": "2024-01-07T22:00:00.123456",
  "task": "Help me write a Python function",
  "prompt_type": "full",
  "task_length": 31,
  "num_contexts_used": 3,
  "context_ids": ["ctx-123", "ctx-456", "ctx-789"],
  "context_types": {
    "preference": 1,
    "goal": 1,
    "document": 1
  },
  "generated_prompt": "Given these contexts:\n\n...",
  "prompt_length": 587,
  "max_contexts_requested": 5
}
```

### API Endpoints

#### Get Prompt Logs
```bash
GET /prompt-logs?limit=100&offset=0&prompt_type=full
```

Parameters:
- `limit`: Maximum logs to return (1-1000, default: 100)
- `offset`: Pagination offset
- `prompt_type`: Filter by type ("full" or "compact")

Response includes pagination info and array of log entries.

#### Get Specific Log
```bash
GET /prompt-logs/{log_id}
```

Returns a single log entry by ID or 404 if not found.

#### Export Logs
```bash
POST /prompt-logs/export
```

Exports all logs to a timestamped JSON file in the `logs/` directory.

Returns:
```json
{
  "message": "Logs exported successfully",
  "filepath": "logs/prompt_logs_20240107_220000.json",
  "timestamp": "2024-01-07T22:00:00.123456"
}
```

#### Clear Logs
```bash
DELETE /prompt-logs
```

Clears all prompt logs. **Use with caution** - this is irreversible for in-memory logs.

Returns the count of logs cleared.

#### Statistics
```bash
GET /stats
```

The main statistics endpoint now includes prompt generation statistics:
```json
{
  "total_contexts": 42,
  "active_contexts": 38,
  "prompt_generation": {
    "total_prompts_generated": 127,
    "full_prompts": 89,
    "compact_prompts": 38,
    "avg_contexts_per_prompt": 3.4,
    "total_contexts_used": 432,
    "most_used_context_types": {
      "preference": 156,
      "goal": 132,
      "document": 89,
      "habit": 55
    }
  }
}
```

## Usage Examples

### Python Client
```python
import requests

# Configure API
BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": "your-api-key"}

# Generate a prompt (automatically logged)
response = requests.post(
    f"{BASE_URL}/generate-prompt",
    json={"task": "Help me plan my week", "max_context_units": 5},
    headers=HEADERS
)
prompt = response.json()

# View recent logs
logs_response = requests.get(
    f"{BASE_URL}/prompt-logs?limit=10",
    headers=HEADERS
)
recent_logs = logs_response.json()["logs"]

# Export all logs
export_response = requests.post(
    f"{BASE_URL}/prompt-logs/export",
    headers=HEADERS
)
print(f"Logs saved to: {export_response.json()['filepath']}")

# Get statistics
stats = requests.get(f"{BASE_URL}/stats", headers=HEADERS).json()
print(f"Total prompts generated: {stats['prompt_generation']['total_prompts_generated']}")
```

### CLI with curl
```bash
# Generate prompt (logged automatically)
curl -X POST http://localhost:8000/generate-prompt \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"task": "Review my project architecture", "max_context_units": 10}'

# View logs
curl http://localhost:8000/prompt-logs?limit=5 \
  -H "X-API-Key: your-api-key"

# Filter by type
curl "http://localhost:8000/prompt-logs?prompt_type=compact&limit=20" \
  -H "X-API-Key: your-api-key"

# Export logs
curl -X POST http://localhost:8000/prompt-logs/export \
  -H "X-API-Key: your-api-key"

# Get specific log
curl http://localhost:8000/prompt-logs/prompt-000042 \
  -H "X-API-Key: your-api-key"
```

## Configuration

### Environment Variables
```bash
# Maximum number of logs to keep in memory
PROMPT_LOG_MAX_SIZE=10000  # Default: 10000
```

### Log Rotation
When the maximum number of logs is reached, the oldest logs are automatically removed (FIFO queue). For long-term storage, use the export functionality regularly.

## Security Considerations

1. **Authentication Required**: All log endpoints require API key authentication
2. **Sensitive Data**: Logs contain full task descriptions and generated prompts - ensure proper access controls
3. **Log Export**: Exported files are saved to the `logs/` directory - secure this directory appropriately
4. **Clear Logs**: The DELETE endpoint is intentionally not restricted, but should be used carefully

## Implementation Details

### PromptLogger Class
Located in `prompt_logger.py`, the `PromptLogger` class manages all logging operations:

- **Thread-safe**: Uses deque for efficient append/pop operations
- **Memory-efficient**: Automatic trimming when max size reached
- **Zero-configuration**: Works out of the box with sensible defaults
- **Type-safe**: Uses dataclasses for log entries

### Integration Points
Logging is integrated at the API level in `main.py`:

1. After prompt composition in `/generate-prompt`
2. After compact prompt composition in `/generate-prompt/compact`
3. Linked to the `/stats` endpoint for aggregated metrics

## Testing

The prompt logging system includes comprehensive tests:

- **14 unit tests** in `test_prompt_logger.py`
- **11 integration tests** in `test_api_prompt_logging.py`
- Tests cover initialization, logging, pagination, filtering, stats, export, and edge cases

Run tests:
```bash
pytest test_prompt_logger.py -v
pytest test_api_prompt_logging.py -v
```

## Future Enhancements

Potential improvements for future versions:

- **Persistent Storage**: Save logs to database or disk
- **Log Retention Policies**: Configurable time-based expiration
- **Search & Filtering**: Full-text search across logs
- **Analytics Dashboard**: Visual insights into prompt patterns
- **Webhook Notifications**: Alert on specific events
- **Log Compression**: Archive old logs efficiently

## Troubleshooting

### Logs Not Appearing
- Verify authentication is working
- Check that prompt generation endpoints are being called successfully
- Review application logs for any errors

### Performance Impact
- In-memory logging is extremely fast (< 1ms overhead)
- If performance issues occur, reduce `PROMPT_LOG_MAX_SIZE`
- Consider periodic exports and clears for long-running instances

### Export File Not Created
- Ensure `logs/` directory exists or can be created
- Check write permissions
- Verify disk space availability

## API Reference Summary

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/prompt-logs` | GET | List logs with pagination | Yes |
| `/prompt-logs/{id}` | GET | Get specific log | Yes |
| `/prompt-logs/export` | POST | Export to JSON file | Yes |
| `/prompt-logs` | DELETE | Clear all logs | Yes |
| `/stats` | GET | Get statistics (includes prompt stats) | Yes |

All endpoints return JSON responses and follow standard HTTP status codes.

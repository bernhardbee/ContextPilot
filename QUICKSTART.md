# ContextPilot - Quick Reference

## Installation

```bash
# Clone or navigate to project
cd ContextPilot

# Make scripts executable (macOS/Linux)
chmod +x *.sh

# Start everything
./start.sh
```

## Quick Commands

### Start Both Backend & Frontend
```bash
./start.sh
```

### Start Backend Only
```bash
./start-backend.sh
# Or manually:
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Start Frontend Only
```bash
./start-frontend.sh
# Or manually:
cd frontend
npm install
npm start
```

### Run Demo
```bash
./demo.sh
```

### Run Tests
```bash
cd backend
python test_api.py
```

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React UI |
| Backend | http://localhost:8000 | API Server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Redoc | http://localhost:8000/redoc | ReDoc UI |

## API Endpoints

### Contexts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contexts` | Create new context |
| GET | `/contexts` | List all contexts |
| GET | `/contexts/{id}` | Get specific context |
| PUT | `/contexts/{id}` | Update context |
| DELETE | `/contexts/{id}` | Delete context |

### Prompts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-prompt` | Generate full prompt |
| POST | `/generate-prompt/compact` | Generate compact prompt |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | Get statistics |
| GET | `/` | Root info |

## cURL Examples

### Create Context
```bash
curl -X POST http://localhost:8000/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "type": "preference",
    "content": "I prefer functional programming",
    "confidence": 0.9,
    "tags": ["programming", "style"]
  }'
```

### List Contexts
```bash
curl http://localhost:8000/contexts
```

### Generate Prompt
```bash
curl -X POST http://localhost:8000/generate-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a sorting function",
    "max_context_units": 5
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

### Delete Context
```bash
curl -X DELETE http://localhost:8000/contexts/{id}
```

## Python API Usage

```python
from models import ContextUnit, ContextType
from storage import context_store
from relevance import relevance_engine
from composer import prompt_composer

# Create a context
context = ContextUnit(
    type=ContextType.PREFERENCE,
    content="I prefer async/await over callbacks",
    confidence=0.95,
    tags=["javascript", "async"]
)

# Generate embedding
embedding = relevance_engine.encode(context.content)

# Store it
context_store.add(context, embedding)

# Generate prompt
task = "Write an async function to fetch data"
ranked = relevance_engine.rank_with_keywords(task, context_store, max_results=5)
prompt = prompt_composer.compose(task, ranked)

print(prompt.generated_prompt)
```

## TypeScript API Usage

```typescript
import { contextAPI } from './api';
import { ContextType } from './types';

// Create context
const newContext = await contextAPI.createContext({
  type: ContextType.PREFERENCE,
  content: "I prefer TypeScript over JavaScript",
  confidence: 0.9,
  tags: ["programming", "languages"]
});

// List contexts
const contexts = await contextAPI.listContexts();

// Generate prompt
const result = await contextAPI.generatePrompt({
  task: "Create a new component",
  max_context_units: 5
});

console.log(result.generated_prompt);
```

## Context Types

| Type | Use For | Example |
|------|---------|---------|
| `preference` | Personal preferences | "I prefer Python over Java" |
| `decision` | Past decisions | "Using PostgreSQL for database" |
| `fact` | Factual information | "I work remotely in PST timezone" |
| `goal` | Objectives | "Build an MVP in 2 weeks" |

## Configuration

### Backend (.env)
```bash
HOST=0.0.0.0
PORT=8000
EMBEDDING_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.8+)
python3 --version

# Recreate venv
rm -rf backend/venv
cd backend && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Check Node version (need 16+)
node --version

# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port already in use
```bash
# Backend (8000)
lsof -ti:8000 | xargs kill -9

# Frontend (3000)
lsof -ti:3000 | xargs kill -9
```

### CORS errors
- Make sure backend is running on port 8000
- Check CORS_ORIGINS in backend/main.py
- Verify frontend is using correct API URL

## File Structure

```
ContextPilot/
├── backend/                   # FastAPI backend
│   ├── main.py               # API server
│   ├── models.py             # Data models
│   ├── storage.py            # Storage layer
│   ├── relevance.py          # Relevance engine
│   ├── composer.py           # Prompt composer
│   ├── example_data.py       # Example data
│   ├── test_api.py           # Tests
│   └── requirements.txt      # Dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── App.tsx           # Main component
│   │   ├── api.ts            # API client
│   │   ├── types.ts          # TypeScript types
│   │   └── App.css           # Styles
│   ├── public/
│   └── package.json          # Dependencies
├── ARCHITECTURE.md            # System design
├── EXAMPLES.md                # Usage examples
├── README.md                  # Main documentation
└── *.sh                       # Start scripts
```

## Dependencies

### Backend
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- pydantic==2.5.3
- sentence-transformers==2.3.1
- numpy==1.26.3
- torch==2.1.2

### Frontend
- react@18.2.0
- typescript@4.9.5
- axios@1.6.5

## Performance Tips

1. **First run is slow** - Downloads ML model (~80MB)
2. **Subsequent runs are fast** - Model is cached
3. **Embedding generation** - ~50-100ms per text
4. **Similarity search** - O(n) with n contexts
5. **Keep contexts focused** - Better relevance with specific contexts

## Best Practices

### Context Management
- ✅ Be specific in content
- ✅ Use descriptive tags
- ✅ Set appropriate confidence
- ✅ Supersede outdated contexts
- ❌ Don't create duplicate contexts
- ❌ Don't use vague descriptions

### Prompt Generation
- ✅ Describe task clearly
- ✅ Adjust max_context_units as needed
- ✅ Review generated prompts
- ❌ Don't rely on too few contexts
- ❌ Don't overload with irrelevant contexts

## Common Use Cases

### Software Development
```bash
# Task: "Implement user authentication"
# Pulls: Tech stack decisions, security preferences, coding style

# Task: "Write unit tests"
# Pulls: Testing framework decisions, coverage goals, style preferences
```

### Writing
```bash
# Task: "Write project documentation"
# Pulls: Communication style, audience preferences, format decisions

# Task: "Draft team update email"
# Pulls: Communication preferences, project goals, team context
```

### Learning
```bash
# Task: "Explain React hooks"
# Pulls: Learning style preferences, experience level, related knowledge
```

## Next Steps

1. **Explore the UI** - http://localhost:3000
2. **Add your contexts** - Start with 5-10 key preferences
3. **Test prompt generation** - Try different tasks
4. **Review EXAMPLES.md** - See detailed use cases
5. **Read ARCHITECTURE.md** - Understand the system

## Support

- 📖 Documentation: See README.md
- 🏗️ Architecture: See ARCHITECTURE.md
- 💡 Examples: See EXAMPLES.md
- 🐛 Issues: Check terminal logs
- 🔧 Debugging: Use /health endpoint

## License

See LICENSE file for details.

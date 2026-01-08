# Database Configuration Guide

ContextPilot supports persistent storage using either SQLite or PostgreSQL.

## Storage Options

### 1. In-Memory Storage (Development Only)
- No persistence between restarts
- Fast and simple
- Set `CONTEXTPILOT_USE_DATABASE=false` in `.env`

### 2. SQLite (Default)
- File-based database
- No additional setup required
- Vector embeddings stored as JSON
- Best for: Development, small deployments, single-machine setups

### 3. PostgreSQL with pgvector
- Production-grade database
- Native vector similarity search with pgvector extension
- Best for: Production, multi-user deployments, large-scale systems

## Quick Start

### SQLite Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (`.env`):
   ```bash
   CONTEXTPILOT_USE_DATABASE=true
   CONTEXTPILOT_DATABASE_URL=sqlite:///./contextpilot.db
   ```

3. **Initialize database**:
   ```bash
   python init_db.py
   ```

4. **Start the server**:
   ```bash
   python main.py
   ```

The database file `contextpilot.db` will be created in the backend directory.

### PostgreSQL Setup

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Install pgvector extension**:
   ```bash
   # macOS
   brew install pgvector
   
   # Ubuntu/Debian
   sudo apt install postgresql-15-pgvector
   ```

3. **Create database and enable extension**:
   ```bash
   psql -U postgres
   ```
   
   In the PostgreSQL console:
   ```sql
   CREATE DATABASE contextpilot;
   \c contextpilot
   CREATE EXTENSION vector;
   \q
   ```

4. **Configure environment** (`.env`):
   ```bash
   CONTEXTPILOT_USE_DATABASE=true
   CONTEXTPILOT_DATABASE_URL=postgresql://postgres:password@localhost/contextpilot
   ```

5. **Initialize database**:
   ```bash
   python init_db.py
   ```

6. **Start the server**:
   ```bash
   python main.py
   ```

## Database Schema

### context_units Table
Stores context information with optional embeddings.

| Column | Type | Description |
|--------|------|-------------|
| id | String | Unique identifier |
| source_type | String | Type of source (file, directory, code_symbol, etc.) |
| name | String | Display name |
| content | Text | Full content |
| metadata | JSON | Additional metadata |
| embedding | Vector/JSON | Embedding vector (pgvector or JSON) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| superseded_by | String | ID of replacement context (nullable) |

### conversations Table
Stores AI conversation metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | String | Unique conversation ID |
| task | String | Initial task/prompt |
| provider | String | AI provider (openai, anthropic) |
| model | String | Model name |
| created_at | DateTime | Creation timestamp |

### messages Table
Stores individual messages in conversations.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Auto-incrementing ID |
| conversation_id | String | Foreign key to conversations |
| role | String | Message role (user, assistant, system) |
| content | Text | Message content |
| timestamp | DateTime | Message timestamp |
| tokens | Integer | Token count (nullable) |
| finish_reason | String | Completion reason (nullable) |

## Migration from In-Memory Storage

If you have an existing deployment using in-memory storage and want to migrate to the database:

1. **Ensure the server is running** with in-memory storage and has populated context

2. **Run the migration script**:
   ```bash
   python migrate_to_db.py
   ```

3. **Verify migration**:
   ```bash
   # Check context count
   curl http://localhost:8002/contexts | jq 'length'
   ```

4. **Update configuration** to use database:
   ```bash
   CONTEXTPILOT_USE_DATABASE=true
   ```

5. **Restart the server**

## Database Management

### Backup SQLite Database
```bash
cp contextpilot.db contextpilot.db.backup
```

### Backup PostgreSQL Database
```bash
pg_dump -U postgres contextpilot > contextpilot_backup.sql
```

### Restore PostgreSQL Database
```bash
psql -U postgres contextpilot < contextpilot_backup.sql
```

### Reset Database
```bash
# Drop all tables and recreate
python -c "from database import drop_db, init_db; drop_db(); init_db()"
```

### View Database Statistics
```bash
# SQLite
sqlite3 contextpilot.db "SELECT COUNT(*) FROM context_units;"

# PostgreSQL
psql -U postgres contextpilot -c "SELECT COUNT(*) FROM context_units;"
```

## Performance Considerations

### SQLite
- **Pros**: Zero setup, portable, fast for read-heavy workloads
- **Cons**: No concurrent writes, limited scalability
- **Best for**: < 10,000 context units, single-user or low-traffic

### PostgreSQL
- **Pros**: Full ACID compliance, concurrent writes, native vector search
- **Cons**: Requires setup and maintenance
- **Best for**: Production, > 10,000 context units, multi-user

### Vector Search Performance
- **SQLite**: Uses JSON arrays, requires full scan for similarity search
- **PostgreSQL with pgvector**: Uses indexed vector operations (HNSW/IVFFlat)
  - 10-1000x faster for large datasets
  - Supports approximate nearest neighbor search

## Troubleshooting

### "table context_units already exists"
The database was already initialized. To reset:
```bash
python -c "from database import drop_db, init_db; drop_db(); init_db()"
```

### PostgreSQL connection refused
Check if PostgreSQL is running:
```bash
# macOS
brew services list | grep postgresql

# Ubuntu/Debian
sudo systemctl status postgresql
```

### pgvector extension not found
Install the pgvector extension:
```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql-15-pgvector
```

Then enable in your database:
```sql
psql -U postgres -d contextpilot -c "CREATE EXTENSION vector;"
```

### Database locked (SQLite)
SQLite doesn't support concurrent writes. Options:
1. Use PostgreSQL for production
2. Reduce concurrent requests
3. Increase timeout in database URL:
   ```
   sqlite:///./contextpilot.db?timeout=30
   ```

## Security Best Practices

1. **Use strong database passwords**: Never use default credentials in production
2. **Restrict database access**: Use firewall rules to limit database access
3. **Enable SSL/TLS**: For PostgreSQL connections over network
4. **Regular backups**: Automate daily backups
5. **Monitor access**: Log and review database access patterns
6. **Update regularly**: Keep PostgreSQL and pgvector updated

## Configuration Reference

All database settings in `.env`:

```bash
# Enable database storage
CONTEXTPILOT_USE_DATABASE=true

# Database connection URL
CONTEXTPILOT_DATABASE_URL=sqlite:///./contextpilot.db
# or
CONTEXTPILOT_DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Show SQL queries in logs (development only)
CONTEXTPILOT_DATABASE_ECHO=false
```

## Future Enhancements

Planned features for database layer:
- Alembic migrations for schema versioning
- Connection pooling optimization
- Read replicas support
- Automated backup scheduling
- Database health monitoring
- Query performance metrics

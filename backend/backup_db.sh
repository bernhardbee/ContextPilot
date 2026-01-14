#!/bin/bash
# Database backup script for ContextPilot

BACKUP_DIR="backups"
DB_FILE="contextpilot.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_FILE}.${TIMESTAMP}.backup"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Error: Database file '$DB_FILE' not found"
    exit 1
fi

# Create backup
echo "📦 Creating backup..."
cp "$DB_FILE" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: $BACKUP_FILE"
    
    # Keep only last 10 backups
    ls -t "${BACKUP_DIR}"/*.backup 2>/dev/null | tail -n +11 | xargs -r rm
    echo "🧹 Cleaned up old backups (keeping last 10)"
    
    # Show backup size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📊 Backup size: $SIZE"
else
    echo "❌ Backup failed"
    exit 1
fi

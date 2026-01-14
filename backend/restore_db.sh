#!/bin/bash
# Database restore script for ContextPilot

BACKUP_DIR="backups"
DB_FILE="contextpilot.db"

# List available backups
echo "📋 Available backups:"
ls -lht "${BACKUP_DIR}"/*.backup 2>/dev/null | awk '{print NR". "$9" ("$5", "$6" "$7" "$8")"}'

if [ $? -ne 0 ] || [ ! "$(ls -A ${BACKUP_DIR}/*.backup 2>/dev/null)" ]; then
    echo "❌ No backups found in ${BACKUP_DIR}/"
    exit 1
fi

# Get user choice
echo ""
read -p "Enter backup number to restore (or 'q' to quit): " choice

if [ "$choice" = "q" ]; then
    echo "Cancelled"
    exit 0
fi

# Get the selected backup file
BACKUP_FILE=$(ls -t "${BACKUP_DIR}"/*.backup 2>/dev/null | sed -n "${choice}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Invalid selection"
    exit 1
fi

echo "📦 Selected backup: $BACKUP_FILE"
read -p "⚠️  This will overwrite the current database. Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Backup current database before restoring
if [ -f "$DB_FILE" ]; then
    CURRENT_BACKUP="${DB_FILE}.before_restore.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up current database to: $CURRENT_BACKUP"
    cp "$DB_FILE" "$CURRENT_BACKUP"
fi

# Restore
echo "🔄 Restoring database..."
cp "$BACKUP_FILE" "$DB_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database restored successfully"
    echo "🔄 Restart the backend server to use the restored database"
else
    echo "❌ Restore failed"
    exit 1
fi

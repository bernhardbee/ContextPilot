#!/bin/bash
# Model Discovery Startup Script for ContextPilot
# Run this script to refresh available AI models

set -e  # Exit on any error

echo "🧭 ContextPilot Model Discovery"
echo "Updating available AI models..."

# Change to project directory
cd "$(dirname "$0")"

# Run model discovery
python3 discover_models.py

echo ""
echo "🎯 Model discovery complete!"
echo "ℹ️  To apply changes:"
echo "   1. Restart the backend server"
echo "   2. Refresh the frontend"
echo ""
echo "💡 Set up a cron job to run this script daily:"
echo "   crontab -e"
echo "   0 6 * * * /path/to/this/script/update_models.sh"
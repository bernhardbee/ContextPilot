#!/bin/bash

# ContextPilot - Stop Script

echo "🛑 Stopping ContextPilot..."
echo ""

# Stop processes by PID files
if [ -f "backend/backend.pid" ]; then
    BACKEND_PID=$(cat backend/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill -9 $BACKEND_PID
        echo "✓ Stopped backend (PID: $BACKEND_PID)"
    fi
    rm backend/backend.pid
fi

if [ -f "frontend/frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill -9 $FRONTEND_PID
        echo "✓ Stopped frontend (PID: $FRONTEND_PID)"
    fi
    rm frontend/frontend.pid
fi

# Also stop any processes on ports 8000 and 3000
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "✓ Cleaned up port 8000" || true
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "✓ Cleaned up port 3000" || true

echo ""
echo "✅ All services stopped"

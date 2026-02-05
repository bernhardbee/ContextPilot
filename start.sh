#!/bin/bash

# ContextPilot - Start Script with Auto-Setup
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🧭 ContextPilot Launcher"
echo "========================"
echo ""

# Check if setup is needed
NEEDS_SETUP=false

if [ ! -d "backend/venv" ] || [ ! -f "backend/contextpilot.db" ] || [ ! -d "frontend/node_modules" ]; then
    NEEDS_SETUP=true
fi

if [ ! -d "backend/venv" ]; then
    echo "⚠️  Backend virtual environment not found"
    NEEDS_SETUP=true
fi

if [ ! -f "backend/contextpilot.db" ]; then
    echo "⚠️  Database not initialized"
    NEEDS_SETUP=true
else
    # Check if database has tables
    TABLES=$(sqlite3 backend/contextpilot.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='context_units';" 2>/dev/null || echo "0")
    if [ "$TABLES" != "1" ]; then
        echo "⚠️  Database tables not initialized"
        NEEDS_SETUP=true
    fi
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not installed"
    NEEDS_SETUP=true
fi

# Run setup if needed
if [ "$NEEDS_SETUP" = true ]; then
    echo ""
    echo "📦 Running initial setup..."
    echo ""
    chmod +x setup.sh
    ./setup.sh
    echo ""
fi

echo "✓ Environment ready!"
echo ""

# Clean up any existing processes on ports 8000 and 3000
echo "🔍 Checking for running instances..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  → Stopped existing backend" || true
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  → Stopped existing frontend" || true
echo ""

# Start services
echo "🚀 Starting services..."
echo ""
echo "Starting backend on http://localhost:8000..."
cd "$SCRIPT_DIR/backend"
nohup "$SCRIPT_DIR/backend/venv/bin/python" main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# Wait for backend to be ready
echo "  → Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
        if [ "$HEALTH" = "healthy" ]; then
            echo "  ✓ Backend is healthy and ready"
            break
        fi
    fi
    if [ $i -eq 30 ]; then
        echo "  ❌ Backend failed to start. Check backend/backend.log for details"
        cat backend/backend.log
        exit 1
    fi
    sleep 1
done

sleep 3

echo ""
echo "Starting frontend on http://localhost:3000..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid

echo ""
echo "✅ ContextPilot is running!"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  Backend  PID: $BACKEND_PID (log: backend/backend.log)"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop: ./stop.sh or kill -9 $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait a bit and open browser
sleep 2
if command -v open >/dev/null 2>&1; then
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:3000
fi

echo "Press Ctrl+C to stop all services"
echo ""

# Trap SIGINT and cleanup
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT

# Wait for both processes
wait

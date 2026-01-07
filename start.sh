#!/bin/bash

# ContextPilot - Setup and Run Script

echo "🧭 ContextPilot Setup & Run"
echo "============================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo "✓ Node.js found: $(node --version)"
echo ""

# Setup Backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "Loading example data..."
python3 -c "from example_data import load_example_data; load_example_data()"

echo "✓ Backend setup complete!"
echo ""

# Setup Frontend
echo "📦 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install --silent
fi

echo "✓ Frontend setup complete!"
echo ""

# Start services
echo "🚀 Starting services..."
echo ""
echo "Starting backend on http://localhost:8000..."
cd ../backend
source venv/bin/activate
python3 main.py &
BACKEND_PID=$!

sleep 3

echo "Starting frontend on http://localhost:3000..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ ContextPilot is running!"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap SIGINT and cleanup
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT

# Wait for both processes
wait

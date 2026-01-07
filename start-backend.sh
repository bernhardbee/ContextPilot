#!/bin/bash

# Quick start script for backend only

echo "🚀 Starting ContextPilot Backend"
echo "================================="
echo ""

cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

echo "Loading example data..."
python3 -c "from example_data import load_example_data; load_example_data()"

echo ""
echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

python3 main.py

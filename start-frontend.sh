#!/bin/bash

# Quick start script for frontend only

echo "🚀 Starting ContextPilot Frontend"
echo "=================================="
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting frontend on http://localhost:3000"
echo "Make sure backend is running on http://localhost:8000"
echo ""

npm start

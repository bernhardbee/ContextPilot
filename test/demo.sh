#!/bin/bash

# ContextPilot - Demo Script
# This script demonstrates the ContextPilot API

echo "🧭 ContextPilot Demo"
echo "==================="
echo ""

API_URL="http://localhost:8000"

echo "1. Health Check"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

echo "2. Get Statistics"
curl -s "$API_URL/stats" | python3 -m json.tool
echo ""

echo "3. List All Contexts"
curl -s "$API_URL/contexts" | python3 -m json.tool
echo ""

echo "4. Generate Prompt for: 'Write a Python function to process user data'"
curl -s -X POST "$API_URL/generate-prompt" \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python function to process user data", "max_context_units": 5}' \
  | python3 -m json.tool
echo ""

echo "5. Generate Prompt for: 'Design a new frontend component'"
curl -s -X POST "$API_URL/generate-prompt" \
  -H "Content-Type: application/json" \
  -d '{"task": "Design a new frontend component", "max_context_units": 5}' \
  | python3 -m json.tool
echo ""

echo "Demo completed!"

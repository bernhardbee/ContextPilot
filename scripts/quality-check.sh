#!/bin/bash

set -e

echo "🔍 Running ContextPilot Frontend Quality Checks..."
echo ""

cd "$(dirname "$0")/../frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# TypeScript checking
echo -e "${YELLOW}→${NC} TypeScript type checking..."
if npm run type-check; then
  echo -e "${GREEN}✓${NC} TypeScript compilation successful"
else
  echo -e "${RED}✗${NC} TypeScript type check failed"
  exit 1
fi

echo ""

# ESLint
echo -e "${YELLOW}→${NC} Linting code..."
if npm run lint; then
  echo -e "${GREEN}✓${NC} ESLint passed (no warnings)"
else
  echo -e "${RED}✗${NC} ESLint failed"
  exit 1
fi

echo ""

# Unit Tests
echo -e "${YELLOW}→${NC} Running unit tests..."
if npm run test:quick; then
  echo -e "${GREEN}✓${NC} All tests passed"
else
  echo -e "${RED}✗${NC} Unit tests failed"
  exit 1
fi

echo ""

# Production Build
echo -e "${YELLOW}→${NC} Building for production..."
if npm run build; then
  echo -e "${GREEN}✓${NC} Production build successful"
else
  echo -e "${RED}✗${NC} Build failed"
  exit 1
fi

echo ""

# Verify build artifacts
if [ ! -f "dist/index.html" ]; then
  echo -e "${RED}✗${NC} Build artifacts missing (index.html not found)"
  exit 1
fi

if [ ! -d "dist/assets" ]; then
  echo -e "${RED}✗${NC} Build artifacts missing (assets directory not found)"
  exit 1
fi

echo -e "${GREEN}✓${NC} Build artifacts verified"

echo ""
echo "=====================================================  "
echo -e "${GREEN}✅ All quality checks passed!${NC}"
echo "====================================================="
echo ""
echo "Summary:"
echo -e "  ${GREEN}✓${NC} TypeScript compilation successful"
echo -e "  ${GREEN}✓${NC} ESLint passed"
echo -e "  ${GREEN}✓${NC} Unit tests passed"
echo -e "  ${GREEN}✓${NC} Production build successful"
echo -e "  ${GREEN}✓${NC} Build artifacts verified"
echo ""

#!/bin/bash
#
# ContextPilot Setup Script
# Automatically sets up the development environment and initializes the database
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_header "ContextPilot Setup"

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Setup Backend
print_header "Backend Setup"

cd "$SCRIPT_DIR/backend"

# Create virtual environment if it doesn't exist or if broken
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
elif [ ! -x "venv/bin/python" ] || [ ! -f "venv/bin/python" ]; then
    print_warning "Virtual environment exists but is broken. Recreating..."
    rm -rf venv
    python3 -m venv venv
    print_success "Virtual environment recreated"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
print_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt --quiet
print_success "Python dependencies installed"

# Check if database exists and has tables
DB_FILE="contextpilot.db"
DB_INITIALIZED=false

if [ -f "$DB_FILE" ]; then
    # Check if tables exist
    TABLES=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='context_units';" 2>/dev/null || echo "0")
    if [ "$TABLES" = "1" ]; then
        DB_INITIALIZED=true
        print_success "Database already initialized"
    fi
fi

# Initialize database if needed
if [ "$DB_INITIALIZED" = false ]; then
    print_info "Initializing database..."
    python init_db.py
    
    # Stamp with Alembic
    if command_exists alembic; then
        print_info "Setting up database migrations..."
        alembic stamp head 2>/dev/null || true
    fi
    
    print_success "Database initialized"
fi

# Setup Frontend
print_header "Frontend Setup"

cd "$SCRIPT_DIR/frontend"

# Install npm dependencies if node_modules doesn't exist or is incomplete
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    print_info "Installing Node.js dependencies..."
    npm install --quiet
    print_success "Node.js dependencies installed"
else
    print_info "Node.js dependencies already installed"
fi

# Final Summary
print_header "Setup Complete!"

echo ""
print_success "Backend environment is ready"
print_success "Frontend environment is ready"
print_success "Database is initialized"
echo ""
print_info "To start the application:"
echo ""
echo "  ${GREEN}Backend:${NC}  cd backend && venv/bin/python main.py"
echo "  ${GREEN}Frontend:${NC} cd frontend && npm start"
echo ""
echo "  ${GREEN}Or use:${NC}   ./start.sh"
echo ""
print_info "API Documentation: http://localhost:8000/docs"
print_info "Web Interface: http://localhost:3000"
echo ""

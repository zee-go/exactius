#!/bin/bash
# Start the Exactius FastAPI backend server

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file. Please edit it with your configuration."
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for GOOGLE_CLOUD_PROJECT
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT not set in .env"
    echo ""
    echo "Please set GOOGLE_CLOUD_PROJECT in your .env file:"
    echo "  GOOGLE_CLOUD_PROJECT=your-project-id"
    echo ""
    echo "See docs/google-secret-manager-setup.md for setup instructions."
    exit 1
fi

echo "🚀 Starting Exactius API Server"
echo "================================"
echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "API Docs: http://localhost:8000/docs"
echo "================================"
echo ""

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo ""
fi

# Start server
python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

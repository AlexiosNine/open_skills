#!/bin/bash
# Start script for OpenSkill Skill Host

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Get host and port from environment or use defaults
HOST=${OPENSKILL_HOST:-127.0.0.1}
PORT=${OPENSKILL_PORT:-8000}

echo "🚀 Starting OpenSkill Skill Host..."
echo "📍 Server will be available at http://${HOST}:${PORT}"
echo ""

# Start the server
uvicorn src.app:app --host "$HOST" --port "$PORT" --reload


#!/bin/bash
# macOS-specific start script for OpenSkill Skill Host

set -e  # Exit on error

# Colors for macOS terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo -e "${YELLOW}⚠️  Warning: This script is optimized for macOS${NC}"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found${NC}"
    echo ""
    echo "Please run setup first:"
    echo "  ./scripts/setup-macos.sh"
    echo "  or"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Get host and port from environment or use defaults
HOST=${OPENSKILL_HOST:-127.0.0.1}
PORT=${OPENSKILL_PORT:-8000}
BASE_URL="http://${HOST}:${PORT}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Starting OpenSkill Skill Host${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📍 Server: ${GREEN}${BASE_URL}${NC}"
echo -e "📊 Health: ${GREEN}${BASE_URL}/health${NC}"
echo -e "📚 API Docs: ${GREEN}${BASE_URL}/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Function to open browser on macOS
open_browser() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        sleep 2  # Wait for server to start
        open "${BASE_URL}/docs" 2>/dev/null || true
    fi
}

# Open browser in background (optional, can be disabled)
if [ "${OPEN_BROWSER:-1}" = "1" ]; then
    open_browser &
fi

# Start the server
uvicorn src.app:app --host "$HOST" --port "$PORT" --reload


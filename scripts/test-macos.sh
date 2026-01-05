#!/bin/bash
# macOS-specific test script

set -e  # Exit on error

# Colors for macOS terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
TRACE_ID=${1:-test-$(date +%s)}
TEXT=${2:-hello}

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🧪 Testing OpenSkill Skill Host${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📍 Base URL: ${GREEN}${BASE_URL}${NC}"
echo -e "🔍 Trace ID: ${GREEN}${TRACE_ID}${NC}"
echo -e "📝 Text: ${GREEN}${TEXT}${NC}"
echo ""

# Test health endpoint
echo -e "${YELLOW}1. Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health" || echo "ERROR")
if [[ "$HEALTH_RESPONSE" == *"ok"* ]]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "   Make sure the server is running: ./scripts/start-macos.sh"
    exit 1
fi

echo ""

# Test root endpoint
echo -e "${YELLOW}2. Testing root endpoint...${NC}"
ROOT_RESPONSE=$(curl -s "${BASE_URL}/" || echo "ERROR")
if [[ "$ROOT_RESPONSE" == *"skills"* ]]; then
    echo -e "${GREEN}✅ Root endpoint OK${NC}"
    echo "$ROOT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ROOT_RESPONSE"
else
    echo -e "${RED}❌ Root endpoint failed${NC}"
    exit 1
fi

echo ""

# Test echo skill
echo -e "${YELLOW}3. Testing echo skill...${NC}"
RESPONSE=$(curl -s -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}" \
  -d "{\"input\": {\"text\": \"${TEXT}\"}}")

if [[ "$RESPONSE" == *"success"* ]] && [[ "$RESPONSE" == *"true"* ]]; then
    echo -e "${GREEN}✅ Echo skill test passed${NC}"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}❌ Echo skill test failed${NC}"
    echo "$RESPONSE"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""


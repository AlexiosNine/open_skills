#!/bin/bash
# Test script for Agent API

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
PROVIDER=${1:-openai}
MESSAGE=${2:-"echo hello"}

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🤖 Testing Agent API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📍 Base URL: ${GREEN}${BASE_URL}${NC}"
echo -e "🔧 Provider: ${GREEN}${PROVIDER}${NC}"
echo -e "💬 Message: ${GREEN}${MESSAGE}${NC}"
echo ""

# Check if server is running
if ! curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Please start the server first: ./scripts/start-macos.sh"
    exit 1
fi

# Test agent chat
echo -e "${YELLOW}Sending request to Agent...${NC}"
echo ""

RESPONSE=$(curl -s -X POST "${BASE_URL}/agent/chat" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: agent-test-$(date +%s)" \
  -d "{
    \"message\": \"${MESSAGE}\",
    \"provider\": \"${PROVIDER}\",
    \"max_tool_calls\": 5,
    \"max_tokens\": 2000
  }")

# Check if response contains success
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ Agent request successful${NC}"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}❌ Agent request failed${NC}"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

echo ""


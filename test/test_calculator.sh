#!/bin/bash
# Test script for calculator skill via Agent API

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
PROVIDER=${1:-qwen}
NUMBERS=${2:-"1,2,5,6.7,3.3,9"}

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🧮 Testing Calculator via Agent API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📍 Base URL: ${GREEN}${BASE_URL}${NC}"
echo -e "🔧 Provider: ${GREEN}${PROVIDER}${NC}"
echo -e "🔢 Numbers: ${GREEN}${NUMBERS}${NC}"
echo ""

# Check if server is running
if ! curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Please start the server first: ./scripts/start-macos.sh"
    exit 1
fi

# Test agent chat with calculator request
echo -e "${YELLOW}Sending request to Agent...${NC}"
echo ""

# Format message for LLM
MESSAGE="计算这些数字的平均数: ${NUMBERS}"

RESPONSE=$(curl -s -X POST "${BASE_URL}/agent/chat" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: calculator-test-$(date +%s)" \
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
    
    # Extract mean value if available
    MEAN=$(echo "$RESPONSE" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    if data.get('success') and data.get('tool_calls'):
        for tool_call in data['tool_calls']:
            result = tool_call.get('result', {})
            if result.get('success') and result.get('data'):
                results = result['data'].get('results', {})
                if 'mean' in results:
                    print(results['mean'])
                    break
except:
    pass
" 2>/dev/null)
    
    if [ -n "$MEAN" ]; then
        echo ""
        echo -e "${GREEN}📊 Calculated Mean: ${MEAN}${NC}"
    fi
else
    echo -e "${RED}❌ Agent request failed${NC}"
    echo ""
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

echo ""


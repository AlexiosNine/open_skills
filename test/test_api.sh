#!/bin/bash
# Comprehensive API test script

set -e

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
TRACE_ID="test-$(date +%s)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🧪 Comprehensive API Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📍 Base URL: ${GREEN}${BASE_URL}${NC}"
echo -e "🔍 Trace ID: ${GREEN}${TRACE_ID}${NC}"
echo ""

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5
    
    echo -e "${YELLOW}Testing: ${name}${NC}"
    
    if [ -n "$data" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "${method}" "${BASE_URL}${endpoint}" \
          -H "Content-Type: application/json" \
          -H "X-Trace-Id: ${TRACE_ID}" \
          -d "${data}")
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" -X "${method}" "${BASE_URL}${endpoint}" \
          -H "X-Trace-Id: ${TRACE_ID}")
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "${GREEN}✅ ${name} passed (HTTP ${HTTP_CODE})${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ ${name} failed (expected HTTP ${expected_status}, got ${HTTP_CODE})${NC}"
        echo "Response: $BODY"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Health check
test_endpoint "Health Check" "GET" "/health" "" "200"

# Test 2: Root endpoint
test_endpoint "Root Endpoint" "GET" "/" "" "200"

# Test 3: Echo skill - success
test_endpoint "Echo Skill - Success" "POST" "/skills/echo:invoke" \
  '{"input": {"text": "hello"}}' "200"

# Test 4: Echo skill - invalid input
test_endpoint "Echo Skill - Invalid Input" "POST" "/skills/echo:invoke" \
  '{"input": {"text": ""}}' "200"  # Still 200, but success=false in body

# Test 5: Non-existent skill
test_endpoint "Non-existent Skill" "POST" "/skills/nonexistent:invoke" \
  '{"input": {}}' "200"  # Still 200, but success=false in body

# Test 6: Invalid JSON
echo -e "${YELLOW}Testing: Invalid JSON${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}" \
  -d '{"invalid": json}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✅ Invalid JSON test passed (HTTP ${HTTP_CODE})${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Invalid JSON test failed (got HTTP ${HTTP_CODE})${NC}"
    ((FAILED++))
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "✅ Passed: ${GREEN}${PASSED}${NC}"
echo -e "❌ Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
    exit 1
fi


#!/bin/bash
# Run all tests

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🧪 Running All Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if server is running
BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
if ! curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo ""
    echo "Please start the server first:"
    echo "  ./scripts/start-macos.sh  # macOS"
    echo "  ./scripts/start.sh        # Linux"
    exit 1
fi

echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Test counter
TOTAL=0
PASSED=0
FAILED=0

# Run each test
run_test() {
    local test_name=$1
    local test_script=$2
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    ((TOTAL++))
    
    if bash "$test_script"; then
        echo -e "${GREEN}✅ ${test_name} passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ ${test_name} failed${NC}"
        ((FAILED++))
    fi
    echo ""
}

# Run tests
run_test "API Tests" "./test/test_api.sh"
run_test "Integration Tests" "./test/test_integration.sh"
run_test "Echo Skill Tests" "./test/test_echo_skill.sh"

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Total: ${TOTAL}"
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


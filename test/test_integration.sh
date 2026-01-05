#!/bin/bash
# Integration test - tests the full flow

set -e

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}

echo "🔗 Integration Test"
echo "==================="
echo ""

# Check if server is running
echo "1. Checking if server is running..."
if curl -s -f "${BASE_URL}/health" > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running. Please start it first:"
    echo "   ./scripts/start-macos.sh"
    exit 1
fi

# Get available skills
echo ""
echo "2. Getting available skills..."
SKILLS=$(curl -s "${BASE_URL}/" | python3 -c "import sys, json; data=json.load(sys.stdin); print(','.join(data.get('skills', [])))")
echo "   Available skills: $SKILLS"

# Test echo skill
echo ""
echo "3. Testing echo skill..."
TRACE_ID="integration-test-$(date +%s)"
RESPONSE=$(curl -s -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}" \
  -d '{"input": {"text": "integration test"}}')

SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))")
TRACE_ID_RESPONSE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('trace_id', ''))")

if [ "$SUCCESS" = "True" ] && [ "$TRACE_ID_RESPONSE" = "$TRACE_ID" ]; then
    echo "✅ Echo skill test passed"
    echo "   Trace ID matched: $TRACE_ID"
else
    echo "❌ Echo skill test failed"
    echo "   Response: $RESPONSE"
    exit 1
fi

echo ""
echo "✅ Integration test passed!"


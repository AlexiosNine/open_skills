#!/bin/bash
# Test script for echo skill

set -e

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
TRACE_ID="test-$(date +%s)"

echo "🧪 Testing echo skill..."
echo "📍 Base URL: $BASE_URL"
echo "🔍 Trace ID: $TRACE_ID"
echo ""

# Test 1: Basic echo
echo "Test 1: Basic echo"
RESPONSE=$(curl -s -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}" \
  -d '{"input": {"text": "hello"}}')

if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Test 1 passed"
else
    echo "❌ Test 1 failed"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 2: Empty text (should fail)
echo ""
echo "Test 2: Empty text (should fail)"
RESPONSE=$(curl -s -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}-2" \
  -d '{"input": {"text": ""}}')

if echo "$RESPONSE" | grep -q '"success":false'; then
    echo "✅ Test 2 passed"
else
    echo "❌ Test 2 failed"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 3: Missing text field (should fail)
echo ""
echo "Test 3: Missing text field (should fail)"
RESPONSE=$(curl -s -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: ${TRACE_ID}-3" \
  -d '{"input": {}}')

if echo "$RESPONSE" | grep -q '"success":false'; then
    echo "✅ Test 3 passed"
else
    echo "❌ Test 3 failed"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "✅ All echo skill tests passed!"


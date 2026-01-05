#!/bin/bash
# Test script for echo skill

set -e  # Exit on error

BASE_URL=${OPENSKILL_HTTP_BASE_URL:-http://127.0.0.1:8000}
TRACE_ID=${1:-test-$(date +%s)}
TEXT=${2:-hello}

echo "🧪 Testing echo skill..."
echo "📍 Base URL: $BASE_URL"
echo "🔍 Trace ID: $TRACE_ID"
echo "📝 Text: $TEXT"
echo ""

curl -X POST "${BASE_URL}/skills/echo:invoke" \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: $TRACE_ID" \
  -d "{\"input\": {\"text\": \"$TEXT\"}}" \
  | python3 -m json.tool

echo ""


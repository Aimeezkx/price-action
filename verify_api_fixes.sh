#!/bin/bash

echo "🔧 API Connectivity Fix Verification"
echo "=" | tr -d '\n' && for i in {1..50}; do echo -n "="; done && echo

echo "⏳ Waiting for services to be ready..."
sleep 2

echo
echo "🏥 Testing health endpoints..."

# Test simple health check
echo -n "✅ Simple health check: "
response=$(curl -s -w "%{http_code}" http://localhost:8000/api/health/simple)
http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "$http_code - OK"
    echo "   $(echo "${response%???}" | jq -r '.status // "unknown"')"
else
    echo "$http_code - FAILED"
    echo "   Error: ${response%???}"
fi

# Test deep health check
echo -n "✅ Deep health check: "
response=$(curl -s -w "%{http_code}" http://localhost:8000/api/health/deep)
http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "$http_code - OK"
    echo "   Status: $(echo "${response%???}" | jq -r '.status // "unknown"')"
    echo "   DB: $(echo "${response%???}" | jq -r '.checks.db // "unknown"')"
    echo "   Redis: $(echo "${response%???}" | jq -r '.checks.redis // "unknown"')"
else
    echo "$http_code - FAILED"
    echo "   Error: ${response%???}"
fi

echo
echo "🌐 Testing CORS headers..."
echo -n "✅ CORS preflight: "
response=$(curl -s -w "%{http_code}" -H "Origin: http://localhost:3001" -H "Access-Control-Request-Method: GET" -X OPTIONS http://localhost:8000/api/health/simple)
http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "$http_code - OK"
    # Check for CORS headers
    cors_check=$(curl -s -I -H "Origin: http://localhost:3001" -H "Access-Control-Request-Method: GET" -X OPTIONS http://localhost:8000/api/health/simple | grep -i "access-control-allow-origin")
    if [ -n "$cors_check" ]; then
        echo "   CORS headers present: $cors_check"
    else
        echo "   ❌ Missing CORS headers"
    fi
else
    echo "$http_code - FAILED"
fi

echo
echo "📁 Testing upload endpoint..."
echo "Test PDF content for upload testing" > /tmp/test_upload.pdf
echo -n "✅ Upload test: "
response=$(curl -s -w "%{http_code}" -X POST -F "file=@/tmp/test_upload.pdf" http://localhost:8000/api/ingest)
http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "$http_code - OK"
    echo "   Filename: $(echo "${response%???}" | jq -r '.filename // "unknown"')"
    echo "   Size: $(echo "${response%???}" | jq -r '.size // "unknown"') bytes"
    echo "   Status: $(echo "${response%???}" | jq -r '.status // "unknown"')"
else
    echo "$http_code - FAILED"
    echo "   Error: ${response%???}"
fi

echo
echo "📄 Testing documents endpoint..."
echo -n "✅ Documents list: "
response=$(curl -s -w "%{http_code}" http://localhost:8000/api/documents)
http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "$http_code - OK"
    doc_count=$(echo "${response%???}" | jq '. | length')
    echo "   Found $doc_count documents"
else
    echo "$http_code - FAILED"
    echo "   Error: ${response%???}"
fi

echo
echo "✅ Test completed!"
echo
echo "Next steps:"
echo "1. Check docker-compose logs if any tests failed"
echo "2. Open http://localhost:3001 to test frontend"
echo "3. Try uploading a document through the UI"
echo "4. Frontend should now work without CORS errors"

# Clean up
rm -f /tmp/test_upload.pdf
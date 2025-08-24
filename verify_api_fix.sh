#!/bin/bash

echo "API Connectivity Fix Verification"
echo "================================="
echo

# Create a test file
echo "hello world" > /tmp/test_upload.txt

echo "1. Testing direct backend health check..."
curl -i http://localhost:8000/api/health/simple
echo
echo

echo "2. Testing direct backend ingest..."
curl -i -F "file=@/tmp/test_upload.txt" http://localhost:8000/api/ingest
echo
echo

echo "3. Testing frontend proxy ingest..."
curl -i -F "file=@/tmp/test_upload.txt" http://localhost:3001/api/ingest
echo
echo

echo "4. Checking backend logs for any errors..."
echo "Run: docker compose logs -f backend | tail -n 20"
echo

# Clean up
rm -f /tmp/test_upload.txt

echo "Verification complete!"
echo
echo "Expected results:"
echo "- All endpoints should return 200 status"
echo "- Ingest should return {\"ok\": true, ...}"
echo "- No 500 errors or stack traces in logs"
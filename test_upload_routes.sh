#!/bin/bash
# Test if upload routes are available

echo "Testing upload routes..."
echo ""

# Test upload-history endpoint
echo "1. Testing GET /api/upload-history:"
response=$(curl -s http://localhost:8000/api/upload-history)
if echo "$response" | grep -q "files"; then
    echo "   ✅ Upload history endpoint is working!"
    echo "   Response: $response"
else
    echo "   ❌ Upload history endpoint not found"
    echo "   Response: $response"
    echo ""
    echo "   The backend server needs to be restarted to load the new routes."
    echo "   Please run: ./start_backend.sh"
fi

echo ""
echo "2. Check API docs at: http://localhost:8000/docs"
echo "   Look for '/api/upload-data' (POST) and '/api/upload-history' (GET)"


#!/bin/bash
# tests/load/create_view_autocannon.sh

echo "Starting load test with autocannon..."

# Install autocannon if not present
if ! command -v autocannon &> /dev/null; then
    echo "Installing autocannon..."
    npm install -g autocannon
fi

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com", "password":"password123"}' \
  | jq -r '.access_token')

echo "Token obtained: ${TOKEN:0:20}..."

# Load test: Create stories
echo -e "\n📊 Load test: Creating stories"
autocannon -c 10 -d 30 -m POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -b '{"text":"Load test story","visibility":"public"}' \
  http://localhost:8000/api/v1/stories

# Load test: Get feed
echo -e "\n📊 Load test: Getting feed"
autocannon -c 20 -d 30 \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/stories

echo -e "\n✅ Load test completed!"

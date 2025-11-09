#!/bin/bash
# Start React frontend development server

cd "$(dirname "$0")/frontend"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting frontend development server..."
echo "Frontend will be available at: http://localhost:5173"
echo ""

npm run dev


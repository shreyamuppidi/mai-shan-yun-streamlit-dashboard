#!/bin/bash
# Script to restart the backend server

echo "Stopping any running backend servers..."
pkill -f "uvicorn.*app.main" || pkill -f "python.*app.main" || true
sleep 2

echo "Starting backend server..."
cd "$(dirname "$0")/backend"

# Activate venv
if [ -f "../msy/bin/activate" ]; then
    source ../msy/bin/activate
else
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

# Run with reload
echo "Starting server on http://localhost:8000"
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

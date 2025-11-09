#!/bin/bash
# Start FastAPI backend server

cd "$(dirname "$0")/backend"

# Try to activate msy venv, otherwise create and activate local venv
if [ -f "../msy/bin/activate" ]; then
    source ../msy/bin/activate
else
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

# Install dependencies if needed
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# Set OpenRouter API key if available in .streamlit/secrets.toml
if [ -f "../.streamlit/secrets.toml" ]; then
    export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY ../.streamlit/secrets.toml | cut -d'"' -f2)
fi

# Run the backend with uvicorn for auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


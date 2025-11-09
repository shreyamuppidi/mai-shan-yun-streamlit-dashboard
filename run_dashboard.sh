#!/bin/bash
# Run the MSY dashboard with the virtual environment
# Usage: ./run_dashboard.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source msy/bin/activate

# Run Streamlit
echo "🚀 Starting Mai Shan Yun Dashboard..."
echo "📊 Virtual environment: msy"
echo "🌐 Dashboard will open in your browser at http://localhost:8501"
echo ""

streamlit run app.py



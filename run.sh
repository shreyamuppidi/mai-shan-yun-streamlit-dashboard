#!/bin/bash
# Quick start script for Mai Shan Yun Inventory Dashboard

echo "🍜 Mai Shan Yun Inventory Intelligence Dashboard"
echo "================================================"
echo ""

# Check if data files exist
if [ ! -f "data/ingredients.csv" ]; then
    echo "⚠️  No data files found. Generating sample data..."
    python src/data_generator.py
    echo ""
fi

# Start the dashboard
echo "🚀 Starting dashboard..."
echo "📊 Dashboard will open in your browser at http://localhost:8501"
echo ""
streamlit run app.py




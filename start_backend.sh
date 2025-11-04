#!/bin/bash

echo "🚀 Starting RAG LLM Physics Backend..."
echo "======================================"

cd api

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./deploy.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if model file exists
if [ ! -f "dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf" ]; then
    echo "❌ Model file not found. Please ensure dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf is in the api/ directory."
    exit 1
fi

echo "✅ Starting FastAPI server..."
echo "🌐 Backend will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python main.py 
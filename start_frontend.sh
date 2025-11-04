#!/bin/bash

echo "Starting RAG LLM Physics Frontend..."
echo "======================================="

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not installed. Please run ./deploy.sh first."
    exit 1
fi

echo "Starting React development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm start 
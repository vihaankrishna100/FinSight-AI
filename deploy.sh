#!/bin/bash

echo "🚀 RAG LLM Physics - Deployment Script"
echo "======================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo ""
echo "🔧 Setting up Backend..."
cd api

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy model file if it exists in parent directory
if [ -f "../dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf" ]; then
    echo "Copying model file..."
    cp ../dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf ./
else
    echo "⚠️  Warning: Model file not found. Please ensure dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf is in the api/ directory."
fi

cd ..

# Setup Frontend
echo ""
echo "🔧 Setting up Frontend..."
cd frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo ""
echo "1. Start the backend:"
echo "   cd api"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "🌐 To deploy to Vercel:"
echo "   cd frontend"
echo "   npm install -g vercel"
echo "   vercel"
echo ""
echo "📚 See README.md for detailed instructions" 
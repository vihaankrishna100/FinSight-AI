# Finsight AI

A web application that provides AI-powered financial analysis using Retrieval-Augmented Generation (RAG) combined with real-time news data. Think of it as having a financial analyst that can quickly read through the latest news about any company and give you investment insights.

## What This Does

This app lets you ask questions about any publicly traded company, and it will:
- Fetch the most recent news articles about that company
- Analyze which news is relevant to your specific question
- Generate a comprehensive investment analysis based on that information
- Provide recommendations with supporting evidence

## Features

- Real-time financial news: Automatically fetches the latest news from NewsAPI for any company you search
- Intelligent analysis: Uses embeddings and vector search to find news most relevant to your question
- Investment recommendations: Provides Buy/Hold/Sell recommendations with detailed rationale
- Modern interface: Clean, responsive web interface built with React
- Graph Based Responses: Provides graphical analysis of current stock and allows for visual information
- Progress tracking: See exactly what the system is doing as it processes your request

## Architecture

The application has two main parts:

1. **Backend API** (in the `/api/` folder): A FastAPI server that runs the AI model locally, handles news retrieval, creates embeddings, and performs vector search using FAISS
2. **Frontend** (in the `/frontend/` folder): A React web application that provides the user interface

The backend processes everything locally, which means your data stays on your machine and you don't need to worry about API costs for the AI model itself (though you'll need a NewsAPI key for news data).

## What You'll Need

- Python 3.9 or higher
- Node.js 16 or higher
- At least 8GB of RAM (16GB recommended for better performance)
- A NewsAPI key (free tier gives you 100 requests per day, which is plenty for testing)
- The model file: `dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf` (about 4.4GB)

### Using Your Finetuned LoRA Zip

If you trained a LoRA adapter (for example `qwen2.5-7b-finance-lora.zip`), you cannot load that zip directly with `llama-cpp-python`.

This app requires a `.gguf` model file, so use this flow:
1. Merge LoRA adapter with base HF model on Colab
2. Convert merged model to GGUF
3. Run app with `MODEL_PATH=./your-finetuned-model.gguf`

Full steps are in [LORA_ADAPTER_USAGE.md](LORA_ADAPTER_USAGE.md).

## Getting Started

### Setting Up the Backend

First, let's get the backend running:

```bash
# Go into the api directory
cd api

# Create a virtual environment (this keeps dependencies organized)
python -m venv venv

# Activate it (on Mac/Linux)
source venv/bin/activate
# On Windows, use: venv\Scripts\activate

# Install all the required packages
pip install -r requirements.txt

# Make sure you have the model file in the api directory
# It should be named: dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf
# If you downloaded it elsewhere, copy it here
```

heres the code to start the backend:

```bash
python main.py
```

You should see the model loading (this takes a minute or two), and then it will say the server is running on `http://localhost:8000`. You can check if it's working by visiting `http://localhost:8000/docs` - that's the interactive API documentation.

### Setting Up the Frontend

keep the backend running, but create a new terminal window for the frontend:

```bash
# Go into the frontend directory
cd frontend

# Install all the JavaScript dependencies
npm install

# Start the development server
npm start
```

The frontend will open automatically in your browser at `http://localhost:3000`. If it doesn't, just type it manually



## Configuration

### NewsAPI Key

The NewsAPI key is currently hardcoded in the `api/main.py` file. For production use, you should move it to an environment variable. You can get a free API key from [newsapi.org](https://newsapi.org).

To use an environment variable:
1. Create a `.env` file in the `api/` directory
2. Add: `NEWS_API_KEY=your_key_here`
3. Update the code to read from environment variables (using `python-dotenv`)

### Model Settings

If you want to adjust the model settings (maybe you have a powerful GPU or want different performance), you can modify the settings in `api/main.py`:

```python
llm = Llama(
    model_path="./dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf",
    n_gpu_layers=5,  # Increase this if you have a good GPU
    n_ctx=2048,      # Context window size
    n_batch=128      # Batch size for processing
)
```

## Deployment Options

### Local Development

For development and personal use, running both frontend and backend locally works great. Just make sure you have enough RAM for the model.

### Frontend-Only Deployment (Vercel)

Since Vercel doesn't support running large language models, you can deploy just the frontend there and run the backend on your local machine or another server:

###### Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy the frontend
cd frontend
vercel
```

Don't forget to update the API URL in the frontend config to point to wherever your backend is running.

### Full Stack Deployment

For a full deployment, you'll need:
1. A server that can run Python and handle the large model file (Railway, Render, or your own server work)
2. Update the frontend to point to your deployed backend URL
3. Deploy the frontend to Vercel or similar

## Important Notes

- The model file is about 4.4GB, so make sure you have enough disk space
- Loading the model into memory takes a minute or two on startup
- The NewsAPI free tier has a 100 requests per day limit - enough for testing, but you might want to upgrade for heavy use
- All processing happens locally, so no data is sent to external AI services
- For best performance, use a machine with 16GB+ RAM and preferably a GPU

## How the RAG System Works

This application utilized a RAG-based retrieval system for increased reliable outputs by the LLM. This system utilizes the NewsAPI and yfinance API to get information about a specific stock the user inputs. This is a naive single-stage RAG with hybrid context(unstructures and structured data). 



## License

This project is open source and available under the MIT License.



# RAG LLM Finance - AI Financial Advisor

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

Once everything is installed, start the backend:

```bash
python main.py
```

You should see the model loading (this takes a minute or two), and then it will say the server is running on `http://localhost:8000`. You can check if it's working by visiting `http://localhost:8000/docs` - that's the interactive API documentation.

### Setting Up the Frontend

In a new terminal window (keep the backend running):

```bash
# Go into the frontend directory
cd frontend

# Install all the JavaScript dependencies
npm install

# Start the development server
npm start
```

The frontend will open automatically in your browser at `http://localhost:3000`. If it doesn't, just navigate there manually.

### First Use

1. Open the app in your browser (usually `http://localhost:3000`)
2. Enter a company name (try "Apple", "Tesla", or "Microsoft" to start)
3. Ask a question like "What are the current investment risks and opportunities?"
4. Watch the progress updates as it fetches news and generates analysis
5. Read the comprehensive analysis and recommendations

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

## Troubleshooting

**The model won't load**
- Make sure the model file is in the `api/` directory and named correctly
- Check that you have enough RAM (8GB minimum, 16GB recommended)
- Look at the error message in the terminal for more details

**Can't connect to the backend**
- Make sure the backend is running (check `http://localhost:8000/docs`)
- Check that port 8000 isn't being used by something else
- Look at the browser console for connection errors

**No news articles found**
- Check your NewsAPI key
- Make sure you haven't hit the daily request limit (100 for free tier)
- Try a different company name (some companies might not have recent news)

**Slow responses**
- This is normal - the model needs time to process
- The first request after startup takes longer as the model warms up
- Using a GPU significantly speeds things up

## Performance Tips

- 16GB+ RAM makes a noticeable difference
- GPU acceleration (if available) speeds up inference significantly
- The model is quantized (Q4_K_M) which balances quality and speed
- Consider using a smaller model if speed is more important than quality

## How the RAG System Works (Technical Details)

For those interested in the technical implementation:

1. **News Retrieval**: When you submit a query, the system fetches the 5 most recent news articles from NewsAPI
2. **Embedding Creation**: Each news article is converted into a vector embedding using Sentence Transformers (all-MiniLM-L6-v2)
3. **Vector Storage**: These embeddings are stored in a FAISS index for fast similarity search
4. **Query Embedding**: Your question is also converted into an embedding
5. **Retrieval**: FAISS finds the news articles most similar to your question (top-k retrieval)
6. **Context Building**: The retrieved news is formatted and added to the prompt as context
7. **Generation**: The fine-tuned Dolphin model generates a response based on both its training and the retrieved context

This is a classic RAG pipeline, which is why the application can provide current, relevant information even though the model itself was trained on older data.

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! If you find bugs, have feature ideas, or want to improve the code, feel free to submit a pull request or open an issue.

## Support

If you run into issues, check the troubleshooting section above. For additional help, you can open an issue on GitHub with details about your problem. 
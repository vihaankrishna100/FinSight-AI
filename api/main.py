from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import os
import sys
import time
import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime, timedelta

app = FastAPI(title="RAG LLM Finance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use finetuned model or fallback to original
MODEL_PATH = os.getenv("MODEL_PATH", "./qwen2.5-7b-finance-q4km.gguf")
if not os.path.exists(MODEL_PATH):
    # Try original model as fallback
    MODEL_PATH = "./dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf"

try:
    if os.path.exists(MODEL_PATH):
        print(f"[MODEL] Loading from {MODEL_PATH}...")
        llm = Llama(MODEL_PATH, n_gpu_layers=-1, n_ctx=2048)
        print("[MODEL] Model loaded successfully")
    else:
        print(f"[MODEL] No GGUF model found at {MODEL_PATH}")
        llm = None
except Exception as e:
    print(f"Error loading model: {e}")
    llm = None


try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedder loaded successfully")
except Exception as e:
    print(f"Error loading embedder: {e}")
    embedder = None


embedding_dim = 384
news_index = faiss.IndexFlatL2(embedding_dim)
news_texts = []

NEWS_API_KEY = "ac0a51f5e60740508402c48acec86ff2"  

CONTEXT_WINDOW = 2048
MAX_GENERATE_TOKENS = 512
RESERVED_TOKENS = 50



def fetch_company_news(company_name):

    """Fetch news articles for a specific company."""
    print(f"\n[NEWS REQUEST] Fetching news sources for: {company_name}")
    url = (f"https://newsapi.org/v2/everything?"
           f"q={company_name}&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}&language=en")
    response = requests.get(url)


    if response.status_code == 200:
        data = response.json()
        articles = []
        for article in data.get('articles', []):
            if article.get('title'):
                content = f"{company_name}: {article['title']} - {article.get('description', '')}"
                articles.append(content)

                print(f"[NEWS RECEIVED] {article.get('title', 'No title')[:80]}...")
        
        print(f"[NEWS COMPLETE] Received {len(articles)} news articles for {company_name}")
        return articles
    else:
        print(f"[NEWS ERROR] Failed to fetch news for {company_name}: {response.text}")
        return []

#yfinance API
def get_stock_ticker(company_name):
    #stock ticker conversion
    try:
        ticker = yf.Ticker(company_name.upper())
        # Try to get info to verify ticker exists
        info = ticker.info
        if info and 'symbol' in info:
            return info['symbol']
        # If direct lookup fails, try as ticker
        return company_name.upper()
    except:
        return company_name.upper()

def fetch_stock_data(ticker, period="1y"):
    #historical data fetch
    try:
        print(f"\n[STOCK REQUEST] Fetching stock data for ticker: {ticker}")
        ticker_obj = yf.Ticker(ticker)
        
        # Get historical data
        hist = ticker_obj.history(period=period)
        
        # Get latest info
        info = ticker_obj.info
        
        stock_data = {
            "ticker": ticker,
            "company_name": info.get('longName', ticker),
            "current_price": info.get('currentPrice', 'N/A'),
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
            "average_volume": info.get('averageVolume', 'N/A'),
            "dividend_yield": info.get('dividendYield', 'N/A'),
            "historical_data": hist.to_dict('index'),
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"[STOCK DATA] Retrieved data for {ticker}: ${info.get('currentPrice', 'N/A')}")
        return stock_data
    except Exception as e:
        print(f"[STOCK ERROR] Failed to fetch stock data for {ticker}: {str(e)}")
        return None

def generate_stock_graph(ticker, period="3mo", graph_type="price"):
    """Generate a stock price graph and return as base64-encoded image."""
    try:
        print(f"\n[GRAPH REQUEST] Generating {graph_type} graph for {ticker}")
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=period)
        
        if hist.empty:
            print(f"[GRAPH ERROR] No data available for {ticker}")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if graph_type == "price":
            ax.plot(hist.index, hist['Close'], label='Close Price', linewidth=2, color='#1f77b4')
            ax.fill_between(hist.index, hist['Close'], alpha=0.3, color='#1f77b4')
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.set_title(f'{ticker} - Stock Price ({period})', fontsize=14, fontweight='bold')
        
        elif graph_type == "volume":
            ax.bar(hist.index, hist['Volume'], label='Volume', color='#ff7f0e', alpha=0.7)
            ax.set_ylabel('Volume', fontsize=12)
            ax.set_title(f'{ticker} - Trading Volume ({period})', fontsize=14, fontweight='bold')
        
        elif graph_type == "returns":
            daily_returns = hist['Close'].pct_change() * 100
            colors = ['green' if x > 0 else 'red' for x in daily_returns]
            ax.bar(hist.index, daily_returns, label='Daily Returns %', color=colors, alpha=0.7)
            ax.set_ylabel('Daily Return (%)', fontsize=12)
            ax.set_title(f'{ticker} - Daily Returns ({period})', fontsize=14, fontweight='bold')
        
        ax.set_xlabel('Date', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        print(f"[GRAPH SUCCESS] Generated {graph_type} graph for {ticker}")
        return image_base64
    except Exception as e:
        print(f"[GRAPH ERROR] Failed to generate graph for {ticker}: {str(e)}")
        return None




# information for stock
def build_stock_context(ticker):
    #call for RAG
    stock_data = fetch_stock_data(ticker)
    if not stock_data:
        return ""
    
    context = f"""

Stock Information for {stock_data['company_name']} ({ticker}):
- Current Price: ${stock_data['current_price']}
- Market Cap: ${stock_data['market_cap']}
- P/E Ratio: {stock_data['pe_ratio']}
- 52-Week High: ${stock_data['52_week_high']}
- 52-Week Low: ${stock_data['52_week_low']}
- Dividend Yield: {stock_data['dividend_yield']}

"""
    return context

def update_company_database(company_name):
    """Fetch and embed news for user-selected company."""
    global news_texts, news_index

    print(f"\n[DATABASE UPDATE] Starting database update for: {company_name}")
    news_texts = fetch_company_news(company_name)

    if not news_texts:
        print(f"[WARNING] No news found for {company_name}")
        return False

    if embedder is None:
        print("[ERROR] Embedder not loaded")
        return False

    print(f"[PROCESSING] Creating embeddings for {len(news_texts)} news articles...")
    embeddings = embedder.encode(news_texts)
    news_index = faiss.IndexFlatL2(embedding_dim)
    news_index.add(np.array(embeddings))

    print(f"[SUCCESS] News database updated successfully for {company_name}. Index contains {news_index.ntotal} entries.\n")
    return True

def retrieve_relevant_news(query, top_k=5):
    """Retrieve top-k news articles relevant to the query."""
    if not news_texts:
        return ""

    if embedder is None:
        return ""

    query_emb = embedder.encode([query])
    distances, indices = news_index.search(np.array(query_emb), top_k)

    relevant = [news_texts[idx] for idx in indices[0] if idx < len(news_texts)]
    return "\n".join(relevant)

def generate_response(user_query, company_name):
    """Full RAG process: retrieve -> build prompt -> generate."""
    if llm is None:
        return "Model not loaded. Please check the backend setup."

    try:
        relevant_news = retrieve_relevant_news(user_query)
        ticker = get_stock_ticker(company_name)
        stock_context = build_stock_context(ticker)
        
        prompt = f"""You are an AI-powered equity research analyst working at a leading investment firm. Your role is to provide concise, data-driven, and unbiased investment analysis.

Always do the following:
- Use recent news headlines to identify financial risks and opportunities.
- Reference the current stock price, P/E ratio, and other key metrics in your analysis.
- Clearly mention both upside potential and downside risks.
- If applicable, summarize with a Buy / Hold / Sell recommendation.
- Provide a rationale supported by evidence (e.g., earnings, forecasts, partnerships, current valuation).
- Remain objective and professional. Avoid hype or speculation.
- Do not use emojis in your responses. Write in a professional, text-only format.

Recent News about {company_name}:
{relevant_news}

Stock Data:
{stock_context}

User Question: {user_query}

Given the recent news about {company_name} and current stock metrics, please provide your analysis."""
        
        print(f"[GENERATION] Generating response for {company_name}...")
        
        output = llm(prompt, max_tokens=MAX_GENERATE_TOKENS, temperature=0.7, top_p=0.9)
        response_text = output['choices'][0]['text'].strip()
        
        print(f"[GENERATION] Response generated")
        return response_text if response_text else "I'm sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error generating response: {str(e)}"

# --- API ENDPOINTS ---

class ChatRequest(BaseModel):
    company: str
    question: str

class StockRequest(BaseModel):
    ticker: str
    period: str = "1y"

class GraphRequest(BaseModel):
    ticker: str
    period: str = "3mo"
    graph_type: str = "price"  # price, volume, returns

@app.get("/")
async def root():
    return {"message": "RAG LLM Physics API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": llm is not None,
        "embedder_loaded": embedder is not None
    }




@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.company.strip():
        def generate_error():
            yield f"data: {json.dumps({'status': 'error', 'message': 'Please enter a valid company name.'})}\n\n"
        return StreamingResponse(generate_error(), media_type="text/event-stream")
    


    def generate():
        try:
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Fetching latest news sources...'})}\n\n"
            
            if not update_company_database(request.company):
                yield f"data: {json.dumps({'status': 'error', 'message': f'Sorry, no recent news found for {request.company}.'})}\n\n"
                return
            
            
            yield f"data: {json.dumps({'status': 'progress', 'message': f'Received {len(news_texts)} news articles. Analyzing relevant information...'})}\n\n"
            
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Generating AI analysis based on the news...'})}\n\n"
            
            response = generate_response(request.question, request.company)
            
            yield f"data: {json.dumps({'status': 'complete', 'response': response, 'company': request.company, 'question': request.question})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")




@app.post("/stock/data")
async def get_stock_info(request: StockRequest):
    #Fetch real-time stock data for a given ticker.
    ticker = request.ticker.upper()
    stock_data = fetch_stock_data(ticker, request.period)

    #error handle
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for ticker: {ticker}")
    


    return {
        "success": True,
        "data": {
            "ticker": stock_data['ticker'],
            "company_name": stock_data['company_name'],
            "current_price": stock_data['current_price'],
            "market_cap": stock_data['market_cap'],
            "pe_ratio": stock_data['pe_ratio'],
            "52_week_high": stock_data['52_week_high'],
            "52_week_low": stock_data['52_week_low'],
            "average_volume": stock_data['average_volume'],
            "dividend_yield": stock_data['dividend_yield'],
            "last_updated": stock_data['last_updated']
        }
    }




@app.post("/stock/graph")
async def get_stock_graph(request: GraphRequest):
    #Generate and return a stock graph as base64-encoded imagee to push to fronend
    ticker = request.ticker.upper()
    
    if request.graph_type not in ['price', 'volume', 'returns']:
        raise HTTPException(status_code=400, detail="graph_type must be 'price', 'volume', or 'returns'")
    
    image_base64 = generate_stock_graph(ticker, request.period, request.graph_type)
    #api error
    if not image_base64:
        raise HTTPException(status_code=404, detail=f"Could not generate graph for ticker: {ticker}")
    
    return {
        "success": True,
        "ticker": ticker,
        "graph_type": request.graph_type,
        "period": request.period,
        "image": f"data:image/png;base64,{image_base64}"
    }




@app.get("/stock/search/{company_name}")
async def search_stock(company_name: str):
    """Search for a stock ticker by company name."""
    ticker = get_stock_ticker(company_name)
    stock_data = fetch_stock_data(ticker)
    
    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Could not find stock data for: {company_name}")
    
    return {
        "success": True,
        "company_name": stock_data['company_name'],
        "ticker": stock_data['ticker'],
        "current_price": stock_data['current_price']
    }


if __name__ == "__main__":
    backend_port = int(os.getenv("BACKEND_PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=backend_port)
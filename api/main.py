from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
import sys
import time
import requests
import faiss
import numpy as np
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import json

app = FastAPI(title="RAG LLM Physics API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SETUP ---

# Load Dolphin Llama 8B Q4 model (optimized for Mac M4)
# Make sure to include one with 2048 context length
try:
    llm = Llama(
        model_path="./dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf",
        n_gpu_layers=5,
        use_mlock=True,
        verbose=False,
        n_ctx=2048,
        n_batch=128
    )
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    llm = None

# Load fast embedder
try:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedder loaded successfully")
except Exception as e:
    print(f"Error loading embedder: {e}")
    embedder = None

# Initialize FAISS
embedding_dim = 384
news_index = faiss.IndexFlatL2(embedding_dim)
news_texts = []

# NewsAPI config
NEWS_API_KEY = "ac0a51f5e60740508402c48acec86ff2"  

# Context + token settings
CONTEXT_WINDOW = 2048
MAX_GENERATE_TOKENS = 512
RESERVED_TOKENS = 50

# --- FUNCTIONS ---

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
                # Print each news source received
                print(f"[NEWS RECEIVED] {article.get('title', 'No title')[:80]}...")
        
        print(f"[NEWS COMPLETE] Received {len(articles)} news articles for {company_name}")
        return articles
    else:
        print(f"[NEWS ERROR] Failed to fetch news for {company_name}: {response.text}")
        return []

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

def build_prompt(user_query, company_name):
    """Builds prompt including relevant news and user query."""
    relevant_news = retrieve_relevant_news(user_query)
    system_prompt = """<|im_start|>system
You are an AI-powered equity research analyst working at a leading investment firm. Your role is to provide concise, data-driven, and unbiased investment analysis based on the most recent financial news and market trends.

Always do the following:
- Use recent news headlines to identify financial risks and opportunities.
- Clearly mention both upside potential and downside risks.
- If applicable, summarize with a Buy / Hold / Sell recommendation.
- Provide a rationale supported by evidence (e.g., earnings, forecasts, partnerships).
- Remain objective and professional. Avoid hype or speculation.
- Do not use emojis in your responses. Write in a professional, text-only format.
<|im_end|>"""

    news_context = f"<|im_start|>news analyze this\n{relevant_news}<|im_end|>\n"

    user_prompt = f"<|im_start|>user\n{user_query}\nGiven the recent news about {company_name}, please answer the question above using the news as context.<|im_end|>\n"

    assistant_prompt = "<|im_start|>analyst\n"

    return system_prompt + news_context + user_prompt + assistant_prompt

def generate_response(user_query, company_name):
    """Full RAG process: retrieve -> build prompt -> generate."""
    if llm is None:
        return "Model not loaded. Please check the backend setup."

    prompt = build_prompt(user_query, company_name)

    input_token_estimate = len(prompt.split())
    max_tokens_allowed = CONTEXT_WINDOW - input_token_estimate - RESERVED_TOKENS
    max_tokens_allowed = max(1, min(max_tokens_allowed, MAX_GENERATE_TOKENS))

    try:
        response = llm(prompt, max_tokens=max_tokens_allowed, echo=False)

        if "choices" in response and response["choices"]:
            return response["choices"][0].get("text", "").strip()
        else:
            return "I'm sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error generating response: {str(e)}"

# --- API ENDPOINTS ---

class ChatRequest(BaseModel):
    company: str
    question: str

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
            # Send initial status
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Fetching latest news sources...'})}\n\n"
            
            if not update_company_database(request.company):
                yield f"data: {json.dumps({'status': 'error', 'message': f'Sorry, no recent news found for {request.company}.'})}\n\n"
                return
            
            # Send news received status
            yield f"data: {json.dumps({'status': 'progress', 'message': f'Received {len(news_texts)} news articles. Analyzing relevant information...'})}\n\n"
            
            # Send analyzing status
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Generating AI analysis based on the news...'})}\n\n"
            
            # Generate response
            response = generate_response(request.question, request.company)
            
            # Send final response
            yield f"data: {json.dumps({'status': 'complete', 'response': response, 'company': request.company, 'question': request.question})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
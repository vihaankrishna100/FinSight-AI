import os
import sys
import gradio as gr
import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import yfinance as yf
from llama_cpp import Llama

MODEL_PATH = os.getenv("MODEL_PATH", "./dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf")


def has_lora_adapter_folder(path):
    return os.path.isdir(path) and os.path.exists(os.path.join(path, "adapter_model.safetensors"))


if not os.path.exists(MODEL_PATH):
    print(f"\n[ERROR] Model file not found: {MODEL_PATH}")
    if has_lora_adapter_folder("./qwen2.5-7b-finance-lora"):
        print("\n[INFO] Found LoRA adapter folder: ./qwen2.5-7b-finance-lora")
        print("[INFO] This app uses llama.cpp and requires a merged GGUF model.")
        print("[INFO] Merge LoRA with base model on Colab, convert to GGUF, then set MODEL_PATH.")
    print("\nTo download the model, run:")
    print("  wget -O dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf https://huggingface.co/TheBloke/Dolphin-2.9.2-Qwen-7B-GGUF/resolve/main/dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf")
    sys.exit(1)

try:
    print(f"[MODEL] Loading Dolphin Qwen from {MODEL_PATH}...")
    llm = Llama(MODEL_PATH, n_gpu_layers=-1, n_ctx=2048)
    print("[MODEL] Model loaded successfully")
except Exception as e:
    print(f"[MODEL ERROR] Failed to load model: {e}")
    sys.exit(1)


#creates embeddings of all the information recieved from api calls
embedder = SentenceTransformer('all-MiniLM-L6-v2')


embedding_dim = 384
news_index = faiss.IndexFlatL2(embedding_dim)
news_texts = []


#add to .env later
NEWS_API_KEY = "ac0a51f5e60740508402c48acec86ff2"



def fetch_company_news(company_name):
    """Fetch news articles for a specific company."""
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
        return articles
    else:
        print(f"Failed to fetch news for {company_name}: {response.text}")
        return []



def update_company_database(company_name):
    """Fetch and embed news for user-selected company."""
    global news_texts, news_index

    print(f"[INFO] Fetching news for: {company_name}")
    news_texts = fetch_company_news(company_name)



    if not news_texts:
        print("[WARN] No news found.")
        return False

    embeddings = embedder.encode(news_texts)
    news_index = faiss.IndexFlatL2(embedding_dim)
    news_index.add(np.array(embeddings))



    print(f"[INFO] News database updated for {company_name}.")
    return True



def retrieve_relevant_news(query, top_k=5):
    """Retrieve top-k news articles relevant to the query."""
    if not news_texts:
        return ""

    query_emb = embedder.encode([query])
    distances, indices = news_index.search(np.array(query_emb), top_k)

    relevant = [news_texts[idx] for idx in indices[0] if idx < len(news_texts)]
    return "\n".join(relevant)

def get_stock_data(ticker):
    """Fetch real-time stock data."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = ticker_obj.info
        return f"Current Price: ${info.get('currentPrice', 'N/A')}, P/E Ratio: {info.get('trailingPE', 'N/A')}, Market Cap: ${info.get('marketCap', 'N/A')}"
    except:
        return "Stock data unavailable"

def generate_response(user_query, company_name):
    """Generate response using local Dolphin Qwen model."""
    try:
        relevant_news = retrieve_relevant_news(user_query)
        stock_info = get_stock_data(company_name)
        
        prompt = f"""You are an AI-powered equity research analyst.

Recent News about {company_name}:
{relevant_news}

Stock Data:
{stock_info}

User Question: {user_query}

Provide a concise, data-driven investment analysis."""
        
        print(f"[GENERATION] Generating response for {company_name}...")
        
        output = llm(prompt, max_tokens=300, temperature=0.7, top_p=0.9)
        response_text = output['choices'][0]['text'].strip()
        
        print(f"[GENERATION] ✅ Response generated")
        return response_text if response_text else "Unable to generate response."
        
    except Exception as e:
        print(f"[GENERATION ERROR] {str(e)}")
        return f"Error during generation: {str(e)}"

def chat(company_input, question_input):
    """Handles user input: company + question."""
    if not company_input.strip():
        return "Please enter a valid company name."

    if not update_company_database(company_input):
        return f"Sorry, no recent news found for '{company_input}'."

    return generate_response(question_input, company_input)

iface = gr.Interface(
    fn=chat,
    inputs=[gr.Textbox(label="Company to Track"), gr.Textbox(label="Your Investment Question")],
    outputs="text",
    title="Personalized AI Financial Advisor",
    description="Input a company and get real-time financial insights based on live news"
)

iface.launch(share=True)


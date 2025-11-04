# Install needed packages if not already done
# pip install llama-cpp-python gradio requests sentence-transformers faiss-cpu

import os
import sys
import time
import gradio as gr
import requests
import faiss
import numpy as np
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer




# Load Dolphin Llama 8B Q4 model (optimized for Mac M4)
# Make sure to include one with 2048 context length
llm = Llama(
    model_path="/Users/vihaankrishna/RAG_LLM_Physics/dolphin-2.9.2-qwen2-7b-Q4_K_M.gguf",
    n_gpu_layers=5,
    use_mlock=True,
    verbose=False,
    n_ctx=2048,
    n_batch=128
)

# Load fast embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2')

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
print("Step 1 done")
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
<|im_end|>"""

    news_context = f"<|im_start|>news analyze this\n{relevant_news}<|im_end|>\n"

    user_prompt = f"<|im_start|>user\n{user_query}\nGiven the recent news about {company_name}, please answer the question above using the news as context.<|im_end|>\n"

    assistant_prompt = "<|im_start|>analyst\n"


    return system_prompt + news_context + user_prompt + assistant_prompt

def generate_response(user_query, company_name):
    """Full RAG process: retrieve -> build prompt -> generate."""
    prompt = build_prompt(user_query, company_name)

    input_token_estimate = len(prompt.split())
    max_tokens_allowed = CONTEXT_WINDOW - input_token_estimate - RESERVED_TOKENS
    max_tokens_allowed = max(1, min(max_tokens_allowed, MAX_GENERATE_TOKENS))

    response = llm(prompt, max_tokens=max_tokens_allowed, echo=False)

    if "choices" in response and response["choices"]:
        return response["choices"][0].get("text", "").strip()
    else:
        return "I'm sorry, I couldn't generate a response."
    
    if input_token_estimate + RESERVED_TOKENS >= CONTEXT_WINDOW:
        return "Prompt too long. Please shorten your input."


# --- GRADIO CHATBOT ---

def chat(company_input, question_input):
    #Handles user input: company + question.
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
    description="Input a company and get real-time financial insights based on live news updated "
)

iface.launch(share=True)


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from prompt_builder import build_prompt

SEARCH_URL = "http://localhost:8001/search_hybrid"
OLLAMA_URL = "http://localhost:11434/api/generate"
#OLLAMA_URL = "http://172.17.48.1:11434/api/generate"

#MODEL = "llama3.2:3b"
#MODEL = "mistral:7b"
MODEL = "phi3:3.8b"

def search(query):
    response = requests.get(SEARCH_URL, params={"q": query}, timeout=30)
    response.raise_for_status()
    return response.json()

def ask_mistral(query):
    results = search(query)
    prompt = build_prompt(query, results)

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=300)

    response.raise_for_status()
    return response.json()["response"]

if __name__ == "__main__":
    query = "DataFrame duplicated loses index"
    print(f"Query: {query}\n")
    answer = ask_mistral(query)
    print("Answer:\n")
    print(answer)
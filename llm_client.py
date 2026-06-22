from google import genai
from config import GOOGLE_API_KEY, GOOGLE_MODEL

client = genai.Client(api_key=GOOGLE_API_KEY)

def ask_llm(prompt: str, timeout: int = 60) -> str:
    response = client.models.generate_content(
        model=GOOGLE_MODEL,
        contents=prompt
    )
    return response.text

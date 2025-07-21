import os
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    secret_key = SecretStr(api_key) if api_key else None
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=secret_key)
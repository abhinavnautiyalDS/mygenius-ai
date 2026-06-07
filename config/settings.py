import os

from dotenv import load_dotenv

load_dotenv()

# Chatbot
HF_TOKEN = os.getenv(
    "HF_TOKEN"
)

# Finance Agent
GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

# RAG
GOOGLE_API_KEY = os.getenv(
    "GOOGLE_API_KEY"
)

# SQL + Summarizer
OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

# Stock Retrieval
ALPHA_VANTAGE_API_KEY = os.getenv(
    "ALPHA_VANTAGE_API_KEY"
)
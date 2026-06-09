import os
from dotenv import load_dotenv

# --- Load Environment ---
load_dotenv()

# --- Constants ---
PERSIST_DIR = "./storage"
MODEL_ID = "models/gemma-4-31b-it"
EMBED_MODEL_ID = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- UI Config ---
PAGE_TITLE = "Gemma 4 RAG - Book Chatbot"
PAGE_ICON = "📚"
LAYOUT = "wide"

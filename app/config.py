"""
app/config.py
Loads environment variables and defines file paths for the BiztelAI Copilot.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory: D:\BiztelAI-Copilot
BASE_DIR = Path(__file__).resolve().parent.parent

# Load secret variables from D:\BiztelAI-Copilot\.env
load_dotenv(BASE_DIR / ".env")

# Directories
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
INDEX_DIR = DATA_DIR / "index"
STATIC_DIR = BASE_DIR / "static"

# Ensure data directories exist
PDF_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Index file paths
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
CHUNKS_METADATA_PATH = INDEX_DIR / "chunks_metadata.json"

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()

# Chunking & Retrieval Hyperparameters
CHUNK_SIZE = 900        # Characters per chunk
CHUNK_OVERLAP = 180     # Overlap between chunks so sentences/tables stay connected
TOP_K_RESULTS = 5       # Number of chunks retrieved per question

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
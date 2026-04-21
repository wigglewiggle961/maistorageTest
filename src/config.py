"""Central configuration for the Agentic RAG system.

All environment variables and path constants live here.
Import from this module rather than hardcoding values elsewhere.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
EVAL_DATASET_PATH = DATA_DIR / "eval_dataset_v3.json"
EVAL_RESULTS_PATH = DATA_DIR / "eval_results.json"

# ---------------------------------------------------------------------------
# Ollama / Model config
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemma4:e4b")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "qwen3-embedding:0.6b")
# gemma4:e4b handles vision natively — no separate vision model needed
VISION_MODEL: str = os.getenv("VISION_MODEL", "gemma4:e4b")

# ---------------------------------------------------------------------------
# Retrieval config
# ---------------------------------------------------------------------------
RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "10"))
MAX_CONTEXT_CHUNKS: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

# Number of chunks to expand with context windowing
WINDOW_SIZE: int = 1
# Hard cap on final context chunks sent to the generator
MAX_CONTEXT_CHUNKS: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
# Number of top chunks to expand with context windowing
WINDOW_TOP_K: int = int(os.getenv("WINDOW_TOP_K", "2"))

# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------
CHROMA_COLLECTION: str = "azure_foundry_docs"

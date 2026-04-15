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
EVAL_DATASET_PATH = DATA_DIR / "eval_dataset.json"
EVAL_RESULTS_PATH = DATA_DIR / "eval_results.json"

# ---------------------------------------------------------------------------
# Ollama / Model config
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemma3:4b")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
VISION_MODEL: str = os.getenv("VISION_MODEL", "llava")

# ---------------------------------------------------------------------------
# Retrieval config
# ---------------------------------------------------------------------------
TOP_K: int = int(os.getenv("TOP_K", "5"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------
CHROMA_COLLECTION: str = "azure_foundry_docs"

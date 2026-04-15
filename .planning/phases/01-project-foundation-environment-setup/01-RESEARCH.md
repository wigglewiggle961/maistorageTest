# Phase 1: Research — Project Foundation & Environment Setup

## RESEARCH COMPLETE

**Date:** 2026-04-16
**Phase:** 01-project-foundation-environment-setup

---

## 1. Dependency Compatibility Matrix

All versions confirmed on PyPI as of April 2026:

| Package | Pinned Version | Role |
|---------|---------------|------|
| `langgraph` | `1.1.6` | Agentic orchestration framework |
| `langchain` | `0.3.x` (latest 0.3) | Core LLM abstractions |
| `langchain-community` | `0.3.x` (latest 0.3) | Community integrations (loaders, splitters) |
| `langchain-ollama` | `0.2.x` (latest) | Official Ollama integration for LangChain |
| `chromadb` | `0.6.x` (latest) | Vector store — local persistent |
| `ragas` | `0.4.3` | RAG evaluation framework |
| `ollama` | `0.4.x` (latest) | Python SDK for local Ollama API |
| `streamlit` | `1.44.x` (latest) | Demo UI |
| `python-dotenv` | `1.0.1` | Environment variable loading |
| `pandas` | `2.2.x` | Data handling for eval results |
| `pydantic` | `2.x` (pulled transitively) | Data validation — all packages now on v2 |

> **Note on exact pins:** Use `pip install <package>` to get the latest compatible version, then `pip freeze > requirements.txt` to pin. The planner should generate the requirements.txt scaffold with `>=` minimum bounds, then the developer runs `pip install` and freezes to exact versions.

### Known Compatibility Notes

- **Pydantic v2:** All packages (LangChain ≥0.3, ChromaDB ≥0.6, LangGraph ≥1.0) are fully compatible with Pydantic v2. No mixing with Pydantic v1 packages.
- **LangChain 0.3.x + LangGraph 1.x:** Designed to work together. Use `langchain-ollama` (not the deprecated `langchain-community` OllamaLLM class) for Ollama integration.  
- **ChromaDB on Windows:** Pre-built wheels available for Windows x86-64 — no manual C++ compilation needed. If SQLite version is old (<3.35), ChromaDB may warn but works.
- **RAGAS 0.4.x breaking change:** `LangchainLLMWrapper` and `LangchainEmbeddingsWrapper` are deprecated. Use `llm_factory` with OpenAI-compatible client pointed at local Ollama instead.
- **`ollama` SDK vs `langchain-ollama`:** These serve different purposes. The `ollama` SDK is for direct API calls (used in `verify_models.py`). `langchain-ollama` is for LangChain integration (used in the agent).

### Recommended requirements.txt

```
# Core AI stack
langgraph>=1.1.6
langchain>=0.3.0
langchain-community>=0.3.0
langchain-ollama>=0.2.0
chromadb>=0.6.0

# Evaluation
ragas>=0.4.3
openai>=1.0.0  # Required by ragas for OpenAI-compatible Ollama endpoint

# Ollama SDK (for verify_models.py and direct API calls)
ollama>=0.4.0

# UI
streamlit>=1.44.0

# Utilities
python-dotenv>=1.0.1
pandas>=2.2.0
pathlib2>=2.3.7; python_version < "3.12"  # Only if needed for older Python
```

> **After installing:** run `pip freeze > requirements.txt` to pin exact versions.

---

## 2. Ollama Python SDK — Model Verification

The `ollama` Python SDK connects to the local Ollama server at `http://localhost:11434` by default. The base URL is configurable via the `OLLAMA_HOST` environment variable or by passing a `host` parameter to the client.

### SDK API Patterns

```python
import ollama

# List all pulled models
models_response = ollama.list()
model_names = [m['name'] for m in models_response.get('models', [])]

# Test LLM model (gemma3:4b) — send a minimal generate request
response = ollama.chat(
    model='gemma3:4b',
    messages=[{'role': 'user', 'content': 'ping'}]
)

# Test embedding model (nomic-embed-text) 
embed_response = ollama.embed(
    model='nomic-embed-text',
    input='test'
)
# Returns: {'embeddings': [[float, ...]]}

# Test vision model (llava) — send a text-only request (no image needed for ping)
vision_response = ollama.chat(
    model='llava',
    messages=[{'role': 'user', 'content': 'ping'}]
)
```

### verify_models.py Pattern

```python
#!/usr/bin/env python3
"""Verify all required Ollama models are available and responsive."""
import sys
import ollama

REQUIRED_MODELS = {
    'gemma3:4b': 'chat',       # Primary LLM
    'nomic-embed-text': 'embed', # Embeddings
    'llava': 'chat',            # Vision (ingest only)
}

def check_model_available(model_name: str, available_names: list[str]) -> bool:
    """Check if model name matches any pulled model (handles tag differences)."""
    for name in available_names:
        if name.startswith(model_name.split(':')[0]):
            return True
    return False

def verify_model(model_name: str, model_type: str) -> tuple[bool, str]:
    try:
        if model_type == 'embed':
            result = ollama.embed(model=model_name, input='test')
            if result.get('embeddings'):
                return True, f"✓ {model_name} — returned {len(result['embeddings'][0])} dimensions"
        else:
            result = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': 'ping'}]
            )
            if result.get('message'):
                return True, f"✓ {model_name} — responded OK"
        return False, f"✗ {model_name} — unexpected empty response"
    except Exception as e:
        return False, f"✗ {model_name} — {e}"

def main() -> int:
    print("Checking Ollama connection...")
    try:
        models_response = ollama.list()
        available = [m['name'] for m in models_response.get('models', [])]
        print(f"  Found {len(available)} model(s) pulled\n")
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at http://localhost:11434\n  {e}")
        print("\nMake sure Ollama is running: ollama serve")
        return 1

    all_passed = True
    for model_name, model_type in REQUIRED_MODELS.items():
        if not check_model_available(model_name, available):
            print(f"✗ {model_name} — NOT PULLED (run: ollama pull {model_name})")
            all_passed = False
            continue
        ok, msg = verify_model(model_name, model_type)
        print(f"  {msg}")
        if not ok:
            all_passed = False

    print()
    if all_passed:
        print("All models verified. Environment ready.")
        return 0
    else:
        print("Some models failed. Fix the issues above and re-run.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

**Exit code convention:** 0 = all models OK, 1 = failure. This lets CI/scripts detect failure.

---

## 3. Project Structure

### Recommended Directory Layout

```
maistorageTest/
├── src/                        # Core source modules (imported by scripts + app)
│   ├── config.py               # Central config: paths, model names, env vars
│   ├── vectorstore.py          # ChromaDB wrapper (Phase 2)
│   ├── agent.py                # LangGraph graph definition (Phase 3)
│   └── evaluator.py            # RAGAS evaluation logic (Phase 5)
├── scripts/                    # Runnable entry points
│   ├── verify_models.py        # Phase 1: Ollama health check
│   ├── ingest.py               # Phase 2: Document ingestion
│   └── evaluate.py             # Phase 5: RAGAS evaluation
├── tests/                      # Unit + integration tests
├── data/                       # Persistent outputs (NOT committed)
│   ├── chroma_db/              # ChromaDB persisted collection
│   ├── eval_dataset.json       # FAQ-derived evaluation dataset
│   └── eval_results.json       # RAGAS output
├── docs/                       # Written documentation (Phase 6)
├── documents/                  # Source corpus (already exists — DO NOT MOVE)
│   ├── concepts/
│   ├── how-to/
│   ├── quickstarts/
│   ├── media/
│   ├── overview.md
│   ├── environment-setup.md
│   └── faq.yml
├── app.py                      # Streamlit entry point (Phase 4)
├── requirements.txt            # Pinned dependencies
├── .env.example                # Environment variable template
├── .gitignore
└── README.md
```

### src/ Layout Decision

**Flat layout** — no `__init__.py` in `src/`. Scripts use explicit path manipulation:

```python
# At top of each script in scripts/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
```

This keeps imports simple: `from config import CHROMA_PATH` not `from src.config import CHROMA_PATH`.

### src/config.py Pattern

Central config module — all magic strings live here:

```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
EVAL_DATASET_PATH = DATA_DIR / "eval_dataset.json"
EVAL_RESULTS_PATH = DATA_DIR / "eval_results.json"

# Models
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
VISION_MODEL = os.getenv("VISION_MODEL", "llava")

# Retrieval
TOP_K = int(os.getenv("TOP_K", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ChromaDB
CHROMA_COLLECTION = "azure_foundry_docs"
```

### .gitignore Essentials

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyc
.venv/
venv/
*.egg-info/

# Environment
.env

# Data (generated at runtime — do not commit)
data/chroma_db/
data/eval_dataset.json
data/eval_results.json

# OS
.DS_Store
Thumbs.db
```

---

## 4. RAGAS Local LLM Configuration

RAGAS 0.4.x uses LiteLLM under the hood, which supports Ollama via OpenAI-compatible endpoint.

### Configuration Pattern (Phase 5)

```python
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings import embedding_factory

# Point to local Ollama OpenAI-compatible endpoint
ollama_client = AsyncOpenAI(
    api_key="ollama",  # Ollama ignores the key
    base_url="http://localhost:11434/v1"
)

# Create RAGAS LLM judge
evaluator_llm = llm_factory(
    model="gemma3:4b",
    provider="openai",
    client=ollama_client
)

# Create RAGAS embedder
evaluator_embeddings = embedding_factory(
    model="nomic-embed-text",
    provider="openai",
    client=ollama_client
)
```

> **Note for Phase 5:** The `openai>=1.0.0` package is a required dependency even though we're not using OpenAI — RAGAS uses the `AsyncOpenAI` client class to talk to Ollama's `/v1` endpoint. Add it to requirements.txt.

---

## 5. Windows Considerations

- **Path handling:** Use `pathlib.Path` everywhere. Never hardcode backslashes. `Path(__file__).parent` is portable.
- **ChromaDB:** Pre-built wheels for Windows — no Visual Studio Build Tools needed for modern ChromaDB ≥0.6. SQLite is bundled.
- **Ollama:** Must be running as a background process (`ollama serve` or via the Ollama system tray app). The Python SDK talks to `http://localhost:11434` — same on Windows.
- **Virtual environment activation on Windows:** `.venv\Scripts\activate` (not `source .venv/bin/activate`). README must specify this.
- **Long path issues:** ChromaDB persists to `data/chroma_db/` — avoid deeply nested paths to stay under Windows 260-char limit.

---

## Validation Architecture

### What to validate in Phase 1

| Check | How to verify | Pass condition |
|-------|--------------|----------------|
| Python env installs | `pip install -r requirements.txt` exits 0 | No ImportError |
| All 3 Ollama models respond | `python scripts/verify_models.py` exits 0 | All 3 pass |
| ChromaDB can initialize | Import + create collection in Python | No exception |
| Config module works | `python -c "from src.config import OLLAMA_BASE_URL; print(OLLAMA_BASE_URL)"` | Prints URL |

### Validation Commands

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Verify models
python scripts/verify_models.py

# Smoke-test ChromaDB
python -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma_db'); c.get_or_create_collection('test'); print('ChromaDB OK')"

# Smoke-test config
python -c "import sys; sys.path.insert(0, 'src'); from config import OLLAMA_BASE_URL; print(f'Ollama URL: {OLLAMA_BASE_URL}')"
```

## RESEARCH COMPLETE

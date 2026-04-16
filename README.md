# Agentic RAG — Microsoft Azure AI Foundry Agent Service

A locally-running **Agentic RAG** system that answers questions about the
[Microsoft Azure AI Foundry Agent Service](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
using its official documentation as the knowledge base.

Built with **LangGraph**, **ChromaDB**, and **Ollama** — fully local, no cloud API needed.

---

## What It Does

- Ingests ~35 Azure AI Foundry markdown docs into a persistent ChromaDB vector store
- Answers questions using an agentic retrieval loop: query routing → retrieval →
  relevance grading → generation → hallucination check → re-retrieval if needed
- Demonstrates measurable improvement over naive RAG using **RAGAS** evaluation metrics
- Provides a **Streamlit** chat interface with citations and agent reasoning trace

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | 3.11+ |
| GPU | NVIDIA RTX 3060 6 GB VRAM (or better) |
| RAM | 16 GB recommended |
| Ollama | v0.4+ installed and running |
| OS | Windows 10/11 (instructions below) or Linux |

---

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).

Verify it's running:

```powershell
ollama list
```

### 2. Pull Required Models

Run these commands to download the three required models:

```powershell
# Primary LLM with native vision (~5 GB — requires 6 GB VRAM)
ollama pull gemma4:e4b

# Embedding model (~639 MB)
ollama pull qwen3-embedding:0.6b
```

> **VRAM note:** `gemma4:e4b` handles both text generation and image understanding natively.
> No separate vision model is needed — a single `ollama pull` gets everything.

---

## Setup

### 1. Clone / Download the Project

```powershell
git clone <repo-url>
cd <project-directory>
```

### 2. Create and Activate a Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

> On Linux/macOS: `source .venv/bin/activate`

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

To pin exact versions after install (recommended for reproducibility):

```powershell
pip freeze > requirements.txt
```

### 4. Configure Environment (Optional)

Copy `.env.example` to `.env` and adjust if needed:

```powershell
Copy-Item .env.example .env
```

The defaults work with a standard local Ollama installation. You only need to edit
`.env` if your Ollama runs on a non-standard port or you want to swap models.

### 5. Verify Models

```powershell
python scripts/verify_models.py
```

Expected output when all models are ready:

```
Ollama endpoint: http://localhost:11434
Checking Ollama connection...

  Found 2 model(s) pulled on this machine.

Verifying required models:
------------------------------------------------
  ✓ gemma4:e4b — chat response OK
  ✓ qwen3-embedding:0.6b — embedding OK (1024 dims)
------------------------------------------------

All models verified. Environment ready.
```

---

## Running the System

### Step 1: Ingest Documents

Build the ChromaDB vector store from the `documents/` corpus:

```powershell
python scripts/ingest.py
```

> **First run:** Ingestion takes 5–20 minutes (image understanding uses `gemma4:e4b`'s
> native vision — no llava required).

### Step 2: Launch the Demo

```powershell
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

> **Note:** `scripts/ingest.py` and `app.py` are built in later phases.
> Complete Phase 2 (ingestion) and Phase 4 (UI) before running these.

---

## Project Structure

```
.
├── src/                    # Core source modules
│   └── config.py           # Central config (paths, model names, env vars)
├── scripts/                # Runnable entry points
│   ├── verify_models.py    # Ollama health check  ← start here
│   ├── ingest.py           # Document ingestion (Phase 2)
│   └── evaluate.py         # RAGAS evaluation (Phase 5)
├── tests/                  # Tests
├── data/                   # Generated at runtime (gitignored)
│   └── chroma_db/          # ChromaDB persistent store
├── docs/                   # Written documentation (Phase 6)
├── documents/              # Source corpus (Azure AI Foundry docs — static)
├── app.py                  # Streamlit demo (Phase 4)
├── requirements.txt        # Pinned Python dependencies
├── .env.example            # Environment variable template
└── README.md               # This file
```

---

## Environment Variables

See `.env.example` for all available settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LLM_MODEL` | `gemma4:e4b` | LLM for generation, routing, and vision |
| `EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model |
| `VISION_MODEL` | `gemma4:e4b` | Vision model — same as LLM (native multimodal) |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `MAX_RETRIES` | `3` | Max re-retrieval attempts |

---

## Evaluation

To measure retrieval quality against the FAQ-derived test set:

```powershell
python scripts/evaluate.py
```

Results are written to `data/eval_report.md` and `data/eval_results.json`.

---

## Documentation

- [`docs/research.md`](docs/research.md) — Traditional vs Agentic RAG: design rationale
- [`docs/system-design.md`](docs/system-design.md) — LangGraph node-by-node architecture
- [`docs/qa-methodology.md`](docs/qa-methodology.md) — RAGAS metrics and evaluation approach

---

## Troubleshooting

**Ollama connection refused:**

```powershell
ollama serve
```

**GPU out of memory:**

`gemma4:e4b` is the only large model used. If you see OOM errors, verify no other large
models are loaded: `ollama ps`. Stop unused models with `ollama stop <model>`.

**ChromaDB errors on re-run:**

Delete `data/chroma_db/` and re-run `python scripts/ingest.py`.

**Windows: `activate` not recognized:**

Make sure you're in PowerShell (not cmd). Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.venv\Scripts\activate
```

# Agentic RAG — Microsoft Azure AI Foundry Agent Service Docs

## What This Is

A locally-running Agentic RAG system built on LangGraph that answers questions about the Microsoft Azure AI Foundry Agent Service using its official markdown documentation as the knowledge base. The system features an agentic retrieval loop (query routing, self-correction, multi-step reasoning) and a Streamlit demo interface. It is built as an assessment deliverable demonstrating prototype, documentation, QA methodology, and optimized retrieval with RAGAS evaluation.

## Core Value

A RAG agent that accurately retrieves grounded answers from the Azure AI Foundry docs with demonstrably better accuracy than naive retrieval — proven via RAGAS metrics and FAQ-based test cases.

## Requirements

### Validated

<!-- None yet — ship to validate -->

(None yet — ship to validate)

### Active

- [ ] Document ingestion pipeline processes all markdown files in `documents/` with recursive, markdown-aware chunking
- [ ] Image files in `documents/media/` are summarized using a vision model (llava via Ollama) and stored as text chunks
- [ ] Embeddings generated with `qwen3-embedding:0.6b` via Ollama and stored in a persistent ChromaDB vector store
- [ ] LangGraph agentic flow orchestrates: query routing → retrieval → relevance grading → generation → hallucination check → re-retrieval if needed
- [ ] LLM generation uses `gemma3:4b` via Ollama (fits in 6 GB VRAM)
- [ ] FAQ Q&A pairs from `documents/faq.yml` and `concepts/foundry-iq-faq.yml` are validated against source documents and used as the evaluation dataset
- [ ] RAGAS evaluation harness measures Faithfulness, Answer Relevancy, Context Precision, and Context Recall
- [ ] Streamlit demo interface accepts user questions and displays answers with retrieved source chunks and citations
- [ ] System is fully local — no cloud API calls required
- [ ] Project is containerizable via Docker Compose (Ollama + app containers) for future deployment

### Out of Scope

- Cloud LLM APIs (OpenAI, Anthropic, etc.) — fully local via Ollama is the priority constraint
- User authentication — single-user local demo, no auth needed
- Cloud deployment to a hosting provider — local-first; Docker Compose path exists but cloud hosting is not v1
- Real-time document syncing — corpus is static (the provided `documents/` folder)
- Fine-tuning or RLHF — using pre-trained Ollama models as-is

## Context

- **Assessment scope:** Question 1 from `AssessmentQuestion.md` — Agentic RAG prototype, research writeup, QA explanation, and working demo
- **Document corpus:** ~35 markdown files covering Microsoft Azure AI Foundry Agent Service (setup, concepts, how-to, quickstarts). Also includes `faq.yml` / `foundry-iq-faq.yml` for test case seed Q&A pairs. Images in `documents/media/` (recursively including subdirectories) are architectural diagrams processed at ingest time.
- **Hardware constraints:** RTX 3060 Laptop edition (6 GB VRAM) — model selection must fit within this envelope
- **Prior experience:** Developer has used ChromaDB before; LangGraph is the chosen agentic orchestration framework
- **FAQ answer trust:** Answers in `faq.yml` are considered introductory summaries. Ground truth for evaluation will be cross-verified against the actual markdown documents, not taken from the YAML verbatim
- **Image handling decision:** `gemma4:e4b` (via Ollama) generates text summaries of all images in `documents/media/` recursively at ingest time; summaries become retrievable chunks. `gemma4:e4b` handles vision natively — no separate llava model needed.

## Constraints

- **Hardware:** RTX 3060 Laptop 6 GB VRAM — all models must fit (gemma4:e4b ~5 GB, qwen3-embedding:0.6b ~639 MB)
- **Tech Stack:** Python, LangGraph, ChromaDB, Ollama, Streamlit — no cloud dependencies at runtime
- **Scope:** Single-milestone assessment deliverable — working prototype + demo + docs + QA explanation
- **Corpus:** Static `documents/` folder; no live web scraping or API fetching of Azure docs

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| gemma3:4b as primary LLM | Strong instruction-following in 4B class, fits in 6 GB VRAM, available via Ollama | — Pending |
| `gemma4:e4b` for image summarization at ingest time | Handles vision natively; no separate llava model needed; fits in 6 GB VRAM alongside qwen3-embedding:0.6b | ✓ Confirmed Phase 2 |
| LangGraph for agentic flow | Explicit graph-based control over retrieval loop (grade → re-retrieve → generate) gives fine-grained observability | — Pending |
| ChromaDB for vector store | Developer has prior experience; local persistence, no server needed | — Pending |
| `qwen3-embedding:0.6b` for embeddings | Qwen3 embedding model; Ollama-native; already pulled | ✓ Confirmed Phase 2 |
| Streamlit for demo UI | Python-native, Docker-friendly, no JS required, fast to build and polish | — Pending |
| Recursive markdown-aware chunking | Respects document structure (headers, code blocks); reduces context noise vs fixed-size chunks | — Pending |
| FAQ Q&A cross-verified against docs | Ensures ground truth is faithful to actual documents, not summary-level YAML answers | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-15 after initialization*

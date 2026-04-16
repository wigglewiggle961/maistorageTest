# Phase 2: Document Ingestion Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 02-document-ingestion-pipeline
**Areas discussed:** Chunking Strategy, Vision Model, Image Scope, FAQ Verification, VectorStore Wrapper

---

## Chunking Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| MarkdownHeaderTextSplitter | Splits on header boundaries; structure-aware | ✓ |
| RecursiveCharacterTextSplitter (markdown) | Fixed-size with overlap; less structure-aware | |
| UnstructuredMarkdownLoader | More heavyweight; handles tables/images inline | |

**User's choice:** `MarkdownHeaderTextSplitter` — all heading levels (`#`, `##`, `###`, etc.) anchor splits. Max chunk size 1024 tokens. Code blocks kept intact (do not split mid-block).

**Notes:** When a section exceeds 1024 tokens after header splitting, fall back to `RecursiveCharacterTextSplitter(chunk_size=1024)`. Code block integrity takes priority over strict size limit.

---

## Vision Model for Image Summarization

| Option | Description | Selected |
|--------|-------------|----------|
| gemma4:e4b | Native multimodal; already in config.py as VISION_MODEL | ✓ |
| llava | Separate vision model; was in original roadmap | |

**User's choice:** `gemma4:e4b` — already configured correctly in `src/config.py`. The roadmap, requirements, and project files had stale `llava` references; these were updated as part of this discussion session.

**Notes:** User confirmed `gemma4:e4b` is the correct vision model. `src/config.py` was already correct (`VISION_MODEL = "gemma4:e4b"`). ROADMAP.md, REQUIREMENTS.md, and PROJECT.md updated.

---

## Embedding Model

| Option | Description | Selected |
|--------|-------------|----------|
| qwen3-embedding:0.6b | Qwen3 embed; already pulled by user (~639 MB) | ✓ |
| nomic-embed-text | Was in original roadmap (~274 MB) | |

**User's choice:** `qwen3-embedding:0.6b` — user had already pulled it in Ollama before this discussion.

**Notes:** `src/config.py`, `.env.example`, `README.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and `PROJECT.md` all updated from `nomic-embed-text` to `qwen3-embedding:0.6b`. Historical Phase 1 plan/research artifacts left untouched (they are read-only audit records).

---

## Image Processing Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Top-level only | Only `documents/media/*.png` etc. | |
| Recurse all subdirectories | Walk all of `documents/media/` recursively | ✓ |

**User's choice:** Recurse into all subdirectories.

**Notes:** Subdirectories confirmed in corpus: `agent-identity/`, `memory/`, `monitoring/`, `quickstart/`, `tool-catalog/`, `tools/`. All image files in these dirs to be summarized.

---

## FAQ Evaluation Dataset Verification

| Option | Description | Selected |
|--------|-------------|----------|
| LLM-based cross-check | Call gemma4:e4b to judge if YAML answer is faithful to doc chunks | |
| Simple chunk-overlap heuristic | Token/Jaccard overlap between YAML answer and retrieved chunks | ✓ |

**User's choice:** Simple chunk-overlap heuristic — no LLM call for verification.

**Notes:** Flagged pairs (failed heuristic) are kept in `eval_dataset.json` with `"verified": false` rather than dropped. User is comfortable manually reviewing and curating the dataset.

---

## VectorStore Wrapper

| Option | Description | Selected |
|--------|-------------|----------|
| Thin wrapper | `similarity_search()`, `add_documents()`, `collection_stats()` only | ✓ (agent discretion) |
| Rich wrapper | Add filtering, update, delete, metadata queries | |

**User's choice:** Agent discretion — user was unsure; agent selected thin wrapper.

**Notes:** Thin interface chosen: `similarity_search(query, k)` for Phase 3 retrieval node, `add_documents()` for ingestion, `collection_stats()` for Phase 4 sidebar. Keeps the contract stable and minimal.

---

## Agent's Discretion

- VectorStore wrapper API surface — agent selected thin wrapper (see above)
- Internal module layout in `src/` (flat vs nested ingestion package)
- Image summarization prompt wording
- Whether to parallelize image summarization (sequential chosen for v1)

## Deferred Ideas

- Hybrid retrieval (BM25 + semantic) — ENH-01, v2
- Cross-encoder reranking — ENH-02, v2
- LLM-based FAQ verification — deferred; heuristic chosen for simplicity

# Phase 2: Document Ingestion Pipeline - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse, chunk, embed, and store all markdown documents and image content into a persistent ChromaDB
vector store. Also build the FAQ evaluation dataset by cross-verifying YAML Q&A pairs against source
markdown chunks. Expose the full pipeline as an idempotent CLI (`scripts/ingest.py`).

This phase produces the data layer that every subsequent phase (retrieval, evaluation, demo) depends on.

</domain>

<decisions>
## Implementation Decisions

### Chunking Strategy
- **D-01:** Use `MarkdownHeaderTextSplitter` as the primary splitter.
- **D-02:** **All** heading levels anchor a split — `#`, `##`, `###`, `####`, etc. Any header boundary becomes a chunk boundary.
- **D-03:** Max chunk size: **1024 tokens**. Chunks that exceed 1024 tokens after header-splitting should be further split with `RecursiveCharacterTextSplitter(chunk_size=1024)` as a fallback.
- **D-04:** Code blocks **must not be split mid-block**. If a code block + surrounding prose exceeds 1024 tokens, prefer keeping the code block intact and splitting before/after it rather than inside it.
- **D-05:** Each chunk stores metadata: `source` (relative file path), `section_header` (the header text that anchors the chunk), `chunk_index` (integer position within the source doc).

### Vision Model for Image Summarization
- **D-06:** Use `gemma4:e4b` via Ollama for image summarization (NOT llava). `gemma4:e4b` handles vision natively. `src/config.py` `VISION_MODEL` is already correct.
- **D-07:** ROADMAP.md, REQUIREMENTS.md, and PROJECT.md have been updated to reflect this — all `llava` references replaced.

### Image Processing Scope
- **D-08:** **Recurse into all subdirectories** of `documents/media/`. This includes:
  `agent-identity/`, `memory/`, `monitoring/`, `quickstart/`, `tool-catalog/`, `tools/`.
  All `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` files found anywhere under `documents/media/` are summarized.
- **D-09:** Each image chunk metadata: `source` (relative path from project root, e.g. `documents/media/runtime-components.png`), `type: image_summary`, `section_header` (use the image filename stem, e.g. `runtime-components` — this becomes the citation label in the UI), `chunk_index: 0` (one chunk per image).
  - **Citation path requirement:** The `source` field MUST be the actual image file path so the generation node can cite it correctly. When a retrieved chunk has `type: image_summary`, downstream agents (Phase 3 generation node, Phase 4 UI) will display the image path as the citation source instead of a markdown section header. This is the mechanism that satisfies the citations bonus point for image-derived answers.

### Embedding Model
- **D-10 (updated):** Use `qwen3-embedding:0.6b` via Ollama for all chunk embeddings (NOT nomic-embed-text). Already pulled. `src/config.py` `EMBED_MODEL` is already updated to `"qwen3-embedding:0.6b"`.

### FAQ Evaluation Dataset Verification
- **D-11:** Use a **simple chunk-overlap / text-similarity heuristic** to cross-verify YAML answers against source markdown chunks — NOT an LLM call. A YAML answer is "verified" if its key terms appear with meaningful overlap in the top-k retrieved chunks for that question.
- **D-12:** Pairs that fail the heuristic are **flagged** (marked `"verified": false`) rather than dropped — the user may manually curate/correct them. The output `data/eval_dataset.json` includes both verified and flagged pairs so the user can review.
- **D-13:** Evaluation dataset schema per entry: `{ "question": str, "ground_truth": str, "source_chunks": [str], "verified": bool }`.

### VectorStore Wrapper
- **D-14 (Agent's Discretion):** Thin wrapper class — expose only what downstream phases need:
  - `similarity_search(query: str, k: int) -> List[Document]` — used by the retrieval node (Phase 3)
  - `add_documents(docs: List[Document]) -> None` — used during ingestion
  - `collection_stats() -> dict` — used by the Streamlit sidebar (Phase 4) to show chunk counts
  No filtering, update, or delete capabilities needed for v1.

### Ingestion CLI
- **D-15:** `scripts/ingest.py` runs the full pipeline end-to-end: markdown chunking → image summarization → embedding → ChromaDB upsert → FAQ dataset build.
- **D-16:** Idempotent via content-hash deduplication: `chunk_id = sha256(chunk_text + source_path)`. ChromaDB `upsert` by ID prevents duplicates.
- **D-17:** Progress logging to stdout: chunk counts per doc, total markdown chunks, total image summary chunks, total FAQ pairs (verified vs flagged).

### Agent's Discretion
- Exact prompt wording for image summarization (what to ask `gemma4:e4b` to describe)
- Whether to parallelize image summarization (multiple Ollama calls) or run sequentially — sequential is fine for v1
- Internal module layout within `src/` (e.g., `src/ingestion/`, or flat `src/ingest.py`) — agent decides

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — INGEST-01 through INGEST-08 (all Phase 2 requirements)

### Project Config (already exists — import from here, don't hardcode)
- `src/config.py` — all path constants (`DOCUMENTS_DIR`, `DATA_DIR`, `CHROMA_DIR`, `EVAL_DATASET_PATH`), model names (`LLM_MODEL`, `EMBED_MODEL`, `VISION_MODEL`), and `CHROMA_COLLECTION`

### Corpus Structure
- `documents/` — root of all markdown docs to ingest
- `documents/faq.yml` — primary FAQ source
- `documents/concepts/foundry-iq-faq.yml` — secondary FAQ source
- `documents/media/` — all images to summarize (recurse into subdirectories)

### Prior Phase Decisions
- `.planning/phases/01-project-foundation-environment-setup/01-CONTEXT.md` — flat `src/` layout, `requirements.txt`, Ollama at `localhost:11434`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/config.py` — **must import from here** for all paths and model names. Already has `CHROMA_DIR`, `DOCUMENTS_DIR`, `EMBED_MODEL`, `VISION_MODEL`, `OLLAMA_BASE_URL`, `CHROMA_COLLECTION`, `EVAL_DATASET_PATH`. Do not hardcode any of these elsewhere.

### Established Patterns
- Ollama called at `http://localhost:11434` (from `OLLAMA_BASE_URL` env var via config.py)
- All scripts live in `scripts/`, all importable modules in `src/`
- No Docker — everything runs directly on the host

### Integration Points
- `scripts/ingest.py` is the entry point for this phase — it will be referenced in README.md and Phase 5 evaluation harness
- `VectorStore` wrapper will be imported by Phase 3 (retrieval node) — keep the interface simple and stable
- `data/eval_dataset.json` will be consumed by Phase 5 (`scripts/evaluate.py`)
- `collection_stats()` on the wrapper will be called by Phase 4 (Streamlit sidebar)

</code_context>

<specifics>
## Specific Ideas

- The chunk-overlap heuristic for FAQ verification should check whether key noun phrases from the YAML answer appear in the top retrieved chunks; a simple TF-IDF or token-overlap score (e.g., Jaccard similarity on word sets) is sufficient — no LLM call needed.
- User noted they are comfortable manually reviewing and editing `eval_dataset.json` to fix flagged pairs — so the pipeline doesn't need to be perfect, just transparently flag uncertain pairs.
- Image subdirectories under `documents/media/` include: `agent-identity/`, `memory/`, `monitoring/`, `quickstart/`, `tool-catalog/`, `tools/` — all should be walked recursively.

</specifics>

<deferred>
## Deferred Ideas

- Hybrid retrieval (BM25 + semantic) — v2 enhancement (ENH-01), out of scope for Phase 2
- Cross-encoder reranking — v2 enhancement (ENH-02)
- LLM-based FAQ verification — user opted for simpler heuristic; LLM cross-check can be revisited if heuristic proves unreliable

</deferred>

---

*Phase: 02-document-ingestion-pipeline*
*Context gathered: 2026-04-16*

# Roadmap: Agentic RAG — Azure AI Foundry Docs

**Milestone:** v1.0 — Agentic RAG prototype with RAGAS evaluation and Streamlit demo
**Granularity:** Standard
**Total Phases:** 6

---

## Phase 1: Project Foundation & Environment Setup

**Goal:** Establish the project scaffold, dependency environment, and verify all local models are running via Ollama.
**Requirements:** INFRA-01, INFRA-02, INFRA-03
**UI hint**: no

### Plans

1. Initialize Python project structure — Create `src/`, `tests/`, `data/`, `docs/` layout; set up `pyproject.toml` or `requirements.txt` with all dependencies pinned (LangGraph, langchain, chromadb, streamlit, ragas, ollama-python)
2. Ollama model verification script — Write a `scripts/verify_models.py` script that confirms `gemma3:4b`, `nomic-embed-text`, and `llava` are pulled and responsive via Ollama API
3. Docker Compose scaffold — Create `docker-compose.yml` with `ollama` and `app` service definitions (GPU passthrough for Ollama); app service mounts the project directory
4. README.md — Write setup instructions covering: install Ollama, pull models, install Python deps, run ingestion, run app

### Success Criteria

1. Running `python scripts/verify_models.py` prints successful ping responses from all three Ollama models (gemma3:4b, nomic-embed-text, llava)
2. `docker-compose.yml` exists and passes `docker compose config` validation
3. A new developer can set up the project from scratch following README.md with no undocumented steps

---

## Phase 2: Document Ingestion Pipeline

**Goal:** Parse, chunk, embed, and store all markdown documents and image summaries into a persistent ChromaDB vector store.
**Requirements:** INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05, INGEST-06, INGEST-07, INGEST-08
**UI hint**: no

### Plans

1. Markdown loader & recursive chunker — Use LangChain's `UnstructuredMarkdownLoader` or `MarkdownHeaderTextSplitter` to split all `.md` files in `documents/` respecting headers, code blocks, and tables; attach metadata (source path, section header, chunk index)
2. Image summarization at ingest — For each image in `documents/media/`, call llava via Ollama to generate a text summary; create a `Document` chunk with the summary text and metadata (`source: media/filename.png`, `type: image_summary`)
3. FAQ evaluation dataset builder — Parse `documents/faq.yml` and `documents/concepts/foundry-iq-faq.yml`; for each Q&A pair, retrieve the most relevant markdown chunks and cross-verify the YAML answer matches source doc content; save the verified Q&A pairs to `data/eval_dataset.json`
4. Embedding & ChromaDB persistence — Embed all chunks using `nomic-embed-text` via Ollama; upsert into a persistent ChromaDB collection with deduplication (using chunk content hash as ID); expose a `VectorStore` wrapper class
5. Ingestion CLI — `python scripts/ingest.py` runs the full pipeline end-to-end with progress logging; idempotent (re-run safe)

### Success Criteria

1. Running `python scripts/ingest.py` completes without errors and logs chunk counts: total markdown chunks, total image summary chunks
2. ChromaDB collection persists to disk and can be reopened in a new Python session with all chunks present
3. A similarity search for "What is basic setup vs standard setup?" returns the correct chunks from `environment-setup.md` or `faq.yml`-related docs
4. The `data/eval_dataset.json` file contains valid Q&A pairs with source references
5. Re-running `python scripts/ingest.py` does not duplicate existing chunks

---

## Phase 3: LangGraph Agentic Retrieval Flow

**Goal:** Implement the full agentic RAG graph with query routing, retrieval, grading, generation, hallucination checking, and re-retrieval loop.
**Requirements:** RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06, RAG-07, RAG-08
**UI hint**: no

### Plans

1. LangGraph graph definition — Define the state schema (`AgentState`) and graph structure with nodes: `route_query`, `retrieve`, `grade_documents`, `generate`, `check_hallucination`, `rewrite_query`; define conditional edges for the re-retrieval loop (max retries configurable)
2. Query router node — Classify incoming query as `answerable` (route to retrieval) or `out_of_scope` (return a graceful "I can only answer questions about Azure AI Foundry Agent Service" message)
3. Retrieval & grading nodes — `retrieve` fetches top-k chunks from ChromaDB; `grade_documents` calls gemma3:4b with a relevance prompt and filters chunks below threshold
4. Generation node — `generate` calls gemma3:4b with retrieved context + system prompt to produce a grounded answer; formats citations from chunk metadata
5. Hallucination checker & rewrite node — `check_hallucination` prompts the LLM to verify the answer is supported by the context; `rewrite_query` reformulates the original query for re-retrieval when grading or hallucination check fails

### Success Criteria

1. Asking "What is the difference between basic and standard setup?" returns a correct, cited answer without triggering re-retrieval
2. Asking a question with ambiguous phrasing triggers at least one re-retrieval loop before producing a final answer
3. Asking a completely out-of-scope question (e.g. "What is the capital of France?") returns the graceful out-of-scope message without hallucinating
4. Every answer includes at least one citation (source file name + section header)
5. The LangGraph graph can be visualized (`.get_graph().draw_mermaid()` produces valid output)

---

## Phase 4: Streamlit Demo Interface

**Goal:** Build a polished Streamlit chat interface that surfaces the agent's answers, citations, and reasoning steps to the user.
**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05
**UI hint**: yes

### Plans

1. Streamlit app scaffold — Create `app.py` with page config, chat input widget, and session state for conversation history
2. Answer + citations display — Render the agent's answer in the main chat column; below the answer, show an expandable "Sources" section listing retrieved chunk excerpts with source file and section
3. Agent reasoning trace — Show an expandable "Agent Steps" panel displaying which nodes fired (route → retrieve → grade → generate → [hallucination check] → [rewrite → retrieve again]) so the demo reviewer can see the agentic flow in action
4. Streamlit UX polish — Add a sidebar with: project title, model info (gemma3:4b, nomic-embed-text), corpus info (N chunks indexed), and a "Re-index corpus" button that triggers `ingest.py`

### Success Criteria

1. Running `streamlit run app.py` launches the app in a browser with no errors
2. Typing a question and pressing Enter displays a complete answer with citations within 30 seconds on the target hardware
3. The Sources panel shows at least one retrieved chunk with its source file and section header
4. The Agent Steps panel shows the nodes that fired for the last query
5. The app handles the out-of-scope routing case gracefully (displays the fallback message, no stack trace)

---

## Phase 5: RAGAS Evaluation Harness

**Goal:** Measure retrieval and generation quality using RAGAS metrics against the FAQ-derived evaluation dataset, and demonstrate improvement over a naive baseline.
**Requirements:** EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05
**UI hint**: no

### Plans

1. Naive baseline implementation — Build a simple non-agentic RAG baseline (single retrieval → generate, no grading/hallucination check) to serve as the comparison baseline for RAGAS metrics
2. RAGAS evaluation script — `scripts/evaluate.py` loads `data/eval_dataset.json`, runs each question through both the agentic flow and the baseline, collects `(question, answer, contexts, ground_truth)` tuples, and scores with RAGAS metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall
3. Results report — Generate `data/eval_results.json` and `data/eval_report.md` with per-question scores and aggregate metric averages for both agentic and baseline systems
4. Evaluation dataset validation — Verify that the `eval_dataset.json` ground-truth answers are grounded in the actual markdown docs (not just copied from the YAML); flag any Q&A pairs where the YAML answer diverges significantly from the doc content

### Success Criteria

1. `python scripts/evaluate.py` completes without errors and prints a results table to stdout
2. `data/eval_report.md` contains per-question RAGAS scores for all 4 metrics for both agentic and baseline systems
3. Agentic system scores higher than baseline on at least Faithfulness and Context Precision
4. Evaluation runs fully locally using Ollama models (no OpenAI API calls)

---

## Phase 6: Documentation & Assessment Writeup

**Goal:** Produce the written research discussion and QA methodology explanation required by the assessment, covering Traditional vs Agentic RAG, system design, and test case rationale.
**Requirements:** DOC-01
**UI hint**: no

### Plans

1. Research writeup — `docs/research.md`: explain Traditional RAG (fixed retrieve → generate pipeline) vs Agentic RAG (LangGraph graph with grading, hallucination checking, re-retrieval); discuss why agentic approaches improve accuracy for complex or ambiguous queries
2. System design discussion — `docs/system-design.md`: document the LangGraph node-by-node design decisions, chunking strategy rationale, model selection rationale (gemma3:4b, nomic-embed-text, llava), and ChromaDB vs alternatives
3. QA methodology writeup — `docs/qa-methodology.md`: explain the RAGAS metric selection (what each metric measures and why it matters for RAG quality), the FAQ dataset construction process (cross-verification against source docs), the baseline comparison approach, and known limitations
4. Update README.md — Add links to all docs, add a "Evaluation Results Summary" section with the key RAGAS metric outcomes

### Success Criteria

1. `docs/research.md` clearly articulates at least 4 concrete differences between Traditional RAG and Agentic RAG with examples from this system's implementation
2. `docs/qa-methodology.md` explains all 4 RAGAS metrics and the reasoning for including the naive baseline comparison
3. All docs are written in clear English suitable for a 15-20 minute demo presentation
4. README links to all documentation files and the RAGAS results summary

---

## Milestone Summary

| # | Phase | Requirements | Plans | Status |
|---|-------|-------------|-------|--------|
| 1 | Project Foundation & Environment Setup | 3/3 | Complete   | 2026-04-15 |
| 2 | Document Ingestion Pipeline | INGEST-01–08 | 5 | Pending |
| 3 | LangGraph Agentic Retrieval Flow | RAG-01–08 | 5 | Pending |
| 4 | Streamlit Demo Interface | UI-01–05 | 4 | Pending |
| 5 | RAGAS Evaluation Harness | EVAL-01–05 | 4 | Pending |
| 6 | Documentation & Assessment Writeup | DOC-01 | 4 | Pending |

**Total:** 6 phases | 30 requirements | 26 plans

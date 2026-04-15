# Requirements: Agentic RAG — Azure AI Foundry Docs

**Defined:** 2026-04-15
**Core Value:** A RAG agent that accurately retrieves grounded answers from the Azure AI Foundry docs with demonstrably better accuracy than naive retrieval — proven via RAGAS metrics and FAQ-based test cases.

## v1 Requirements

### Ingestion

- [ ] **INGEST-01**: System processes all markdown files in `documents/` (concepts, how-to, quickstarts) recursively
- [ ] **INGEST-02**: Chunking uses a recursive, markdown-aware splitter that respects headers, code blocks, and tables
- [ ] **INGEST-03**: Each chunk stores metadata (source file path, section header, chunk index) for citation
- [ ] **INGEST-04**: Images in `documents/media/` are summarized by llava via Ollama at ingest time and stored as text chunks with source metadata
- [ ] **INGEST-05**: `faq.yml` and `concepts/foundry-iq-faq.yml` Q&A pairs are parsed; answers are cross-verified against source markdown docs and used as the evaluation dataset
- [ ] **INGEST-06**: Embeddings are generated using `nomic-embed-text` via Ollama
- [ ] **INGEST-07**: Embeddings are stored in a persistent ChromaDB vector store (local disk)
- [ ] **INGEST-08**: Ingestion pipeline is idempotent — re-running does not create duplicate chunks

### Retrieval & Agentic Flow

- [ ] **RAG-01**: LangGraph graph defines the agentic retrieval loop as explicit nodes and edges
- [ ] **RAG-02**: Query routing node classifies whether the question is answerable from the corpus or out-of-scope
- [ ] **RAG-03**: Retrieval node fetches top-k chunks from ChromaDB using semantic similarity
- [ ] **RAG-04**: Relevance grading node scores retrieved chunks and filters low-relevance results
- [ ] **RAG-05**: Generation node produces an answer using `gemma3:4b` via Ollama, grounded only in retrieved context
- [ ] **RAG-06**: Hallucination check node detects if the generated answer contradicts or goes beyond the retrieved context
- [ ] **RAG-07**: Re-retrieval loop triggers (with reformulated query) when relevance grading or hallucination check fails, up to a configurable max retry count
- [ ] **RAG-08**: Answer includes citations: source file names and section headers for each retrieved chunk used

### Evaluation

- [ ] **EVAL-01**: RAGAS evaluation harness measures Faithfulness, Answer Relevancy, Context Precision, and Context Recall
- [ ] **EVAL-02**: Evaluation dataset is derived from FAQ Q&A pairs with answers verified against source documents
- [ ] **EVAL-03**: Evaluation script runs offline (no live LLM API) using the local Ollama models
- [ ] **EVAL-04**: Evaluation results are output as a report (scores per metric + per-question breakdown)
- [ ] **EVAL-05**: System demonstrates measurable improvement over a naive (non-agentic) baseline retrieval on at least Faithfulness and Context Precision

### Demo Interface

- [ ] **UI-01**: Streamlit app provides a chat interface for asking questions about the Azure AI Foundry docs
- [ ] **UI-02**: User can type a question and receive a streamed or displayed answer from the RAG agent
- [ ] **UI-03**: Answer display shows retrieved source chunks and citations (file + section)
- [ ] **UI-04**: UI shows agent reasoning steps (which nodes fired, whether re-retrieval triggered) for demo transparency
- [ ] **UI-05**: UI is runnable locally with a single command (`streamlit run app.py`)

### Infrastructure & Documentation

- [ ] **INFRA-01**: Project includes a `requirements.txt` or `pyproject.toml` with all Python dependencies pinned
- [ ] **INFRA-02**: `README.md` documents setup steps: install Ollama, pull models, run ingestion, run app
- [ ] **INFRA-03**: `docker-compose.yml` is included with Ollama + app containers for future containerized deployment
- [ ] **DOC-01**: Project includes a written discussion covering: thought process, Traditional RAG vs Agentic RAG differences, LangGraph flow design, and QA methodology explanation

## v2 Requirements

### Enhancements

- **ENH-01**: Hybrid retrieval combining semantic + keyword (BM25) for better recall
- **ENH-02**: Cross-encoder reranking of retrieved chunks before generation
- **ENH-03**: Conversational memory — multi-turn chat with history awareness
- **ENH-04**: Cloud deployment of the full stack (Ollama on GPU VM + app container)
- **ENH-05**: Web UI refresh with richer styling and chat history sidebar

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud LLM APIs (OpenAI, Anthropic, etc.) | Fully local via Ollama is a hard constraint |
| User authentication | Single-user local demo; no auth needed |
| Cloud hosting / public deployment | Local-first; Docker Compose path exists but cloud hosting is not v1 |
| Real-time document syncing | Corpus is static (`documents/` folder) |
| Fine-tuning or RLHF | Using pre-trained Ollama models as-is |
| Mobile or native app | Web UI (Streamlit) is sufficient for assessment demo |
| Multi-user / concurrent sessions | Single-user demo scope |

## Traceability

*(Populated during roadmap creation)*

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 2 | Pending |
| INGEST-02 | Phase 2 | Pending |
| INGEST-03 | Phase 2 | Pending |
| INGEST-04 | Phase 2 | Pending |
| INGEST-05 | Phase 2 | Pending |
| INGEST-06 | Phase 2 | Pending |
| INGEST-07 | Phase 2 | Pending |
| INGEST-08 | Phase 2 | Pending |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| RAG-04 | Phase 3 | Pending |
| RAG-05 | Phase 3 | Pending |
| RAG-06 | Phase 3 | Pending |
| RAG-07 | Phase 3 | Pending |
| RAG-08 | Phase 3 | Pending |
| EVAL-01 | Phase 5 | Pending |
| EVAL-02 | Phase 5 | Pending |
| EVAL-03 | Phase 5 | Pending |
| EVAL-04 | Phase 5 | Pending |
| EVAL-05 | Phase 5 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-02 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| UI-04 | Phase 4 | Pending |
| UI-05 | Phase 4 | Pending |
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| DOC-01 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-15 after initial definition*

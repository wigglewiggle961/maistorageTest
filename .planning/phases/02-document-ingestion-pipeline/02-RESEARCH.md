# Phase 2: Document Ingestion Pipeline - Research

## Objective
The objective is to understand how to implement the ingestion pipeline for Phase 2: reading markdown documents, chunking with `MarkdownHeaderTextSplitter`, summarising images using local Ollama (`gemma4:e4b`), cross-verifying YAML FAQ entries against MD content, embedding via `qwen3-embedding:0.6b`, and persisting into a ChromaDB vector store.

## Code & Dependency Analysis
- **Dependencies**: `langchain>=0.3.0`, `langchain-community>=0.3.0`, `chromadb>=0.6.0`, `langchain-ollama>=0.2.0`, `ollama>=0.4.0`, `pyyaml>=6.0.1`.
- **Configuration**: All config is stored in `src/config.py`, providing paths like `DOCUMENTS_DIR`, `DATA_DIR`, `CHROMA_DIR`, `EVAL_DATASET_PATH` and models `OLLAMA_BASE_URL`, `VISION_MODEL` (`gemma4:e4b`), `EMBED_MODEL` (`qwen3-embedding:0.6b`).
- **Data Layout**: 
  - `documents/**/*.md`: Markdown files for ingestion.
  - `documents/media/**/*.png|jpg...`: Images to be summarised.
  - `documents/faq.yml`, `documents/concepts/foundry-iq-faq.yml`: FAQ entries for creating `eval_dataset.json`.

## Technical Approach

### 1. Markdown Chunking & Loader
- **Strategy**: Iterate through all `.md` files in `DOCUMENTS_DIR`.
- **Tool**: `langchain_text_splitters.MarkdownHeaderTextSplitter`. 
- **Headers to split on**: `[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")]`.
- **Fallback split**: `langchain_text_splitters.RecursiveCharacterTextSplitter(chunk_size=1024)` to split long chunks not broken by headers. Code blocks should ideally stay intact.
- **Metadata**: Attach `source` (relative to `DOCUMENTS_DIR`), `section_header` (concatenated from header dictionaries), and `chunk_index`.

### 2. Image Summarization Pipeline
- **Strategy**: Use Python `pathlib` with `rglob` to find all image elements in `documents/media/`.
- **Tool**: The `ollama` Python text generation SDK allows us to execute multimodal prompts, using the `VISION_MODEL` config (`gemma4:e4b`) with `ollama.generate(model=..., images=[encoded_img], prompt=...)`.
- **Chunk Construction**: Once an image is summarized, wrap the summary into a `langchain_core.documents.Document`. Metadata: `source` = relative path, `type: "image_summary"`, `section_header` = image stem, `chunk_index` = 0.

### 3. FAQ Evaluation Dataset Extraction & Verification
- **Strategy**: Read `faq.yml` and `foundry-iq-faq.yml`. 
- **Verification Rule**: Use word overlap (Jaccard similarity) or TF-IDF between FAQ answer and the created markdown Document chunks. Since we need to flag valid overlaps, computing token overlap between the answer's stop-word-filtered nouns against MD chunks will work.
- **Output Schema**: Write out valid JSON to `EVAL_DATASET_PATH`. Elements contain `question`, `ground_truth` (YAML answer), `source_chunks`, and `verified` fields.

### 4. Embedding & Database Storage (ChromaDB)
- **Tool**: `langchain_chroma.Chroma` acting as VectorStore, `langchain_ollama.OllamaEmbeddings` interacting directly with `EMBED_MODEL`, bound to `OLLAMA_BASE_URL`.
- **Idempotency**: Hash `chunk.page_content + chunk.metadata['source']` into a SHA-256 ID, inserting using IDs to prevent duplicates on reruns.

## Implementation Structure
A recommended file layout for this phase is:
- `src/ingestion.py`: Helper functions for splitting markdown and summarising images.
- `src/faq_parser.py`: Helper functions for loading FAQ, applying overlap checking heuristics, and dumping to JSON.
- `src/vectorstore.py`: Abstraction wrapper for ChromaDB that exposes `similarity_search`, `add_documents`, and `collection_stats`.
- `scripts/ingest.py`: Controller script initiating the complete ingestion process and reporting stdout logs.

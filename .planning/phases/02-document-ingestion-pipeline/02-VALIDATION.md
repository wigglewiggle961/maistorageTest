# Phase 2: Document Ingestion Pipeline - Validation
This document defines the validation verification steps necessary to ensure Phase 2 succeeds.

## Verification Requirements

### Core Functionality
- **V-01**: Running `python scripts/ingest.py` must complete successfully, reporting non-zero processed markdown chunks and image chunks.
- **V-02**: Subsequent runs of `python scripts/ingest.py` must take zero additions, maintaining idempotent behaviour without throwing duplicate errors.
- **V-03**: The data folder must contain `eval_dataset.json` formatted securely with fields `question`, `ground_truth`, `source_chunks`, and `verified`.
- **V-04**: The Chroma DB storage must have successfully instantiated in `data/chroma_db` according to `CHROMA_DIR`.

### Code Verification
- **V-05**: VectorStore wrapper contains functions `similarity_search`, `add_documents`, and `collection_stats`.

## Validation Strategy
The test strategy will be using python `-c` test scripts or custom unit tests. However, manual checks via python scripts validating collection stats are appropriate for verifying system health.

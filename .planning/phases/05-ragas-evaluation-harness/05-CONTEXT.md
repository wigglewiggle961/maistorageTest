# Phase 5: RAGAS Evaluation Harness - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure retrieval and generation quality using RAGAS metrics against the FAQ-derived evaluation dataset (`data/eval_dataset.json`), and demonstrate improvement over a naive baseline. The evaluation will run fully locally using existing Ollama models.
</domain>

<decisions>
## Implementation Decisions

### Baseline Architecture
- **D-01:** The naive baseline will use the **exact same** base generation prompt and LLM (`gemma4:e4b`) as the agentic system.
- **D-02:** The only difference from the agent is the absence of the LangGraph agentic nodes (i.e. no routing, no relevance grading, no re-retrieval loops, no hallucination checks).

### RAGAS Judge Models
- **D-03:** Use `gemma4:e4b` natively as the RAGAS LLM judge.
- **D-04:** Use `qwen3-embedding:0.6b` as the RAGAS embedding model.
- **D-05:** Both of these models are reused from previous phases to strictly adhere to the 6GB VRAM constraint. No new models should be pulled.

### Execution Scale and CLI Flags
- **D-06:** The evaluation script (`scripts/evaluate.py`) must support arguments to selectively run questions to speed up testing workflow locally:
  - `--limit N`: Selects only the first N questions from the dataset.
  - `--question N`: Selects a specific question index from the dataset (e.g. `--question 3` runs the 4th item).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` (EVAL-01 through EVAL-05)

### Source Assets
- `data/eval_dataset.json` — The ground truth dataset generated in Phase 2.
- `src/config.py` — For all defined constants and model paths (`LLM_MODEL`, `EMBED_MODEL`, `EVAL_DATASET_PATH`).
</canonical_refs>

<code_context>
## Existing Code Insights

- `scripts/evaluate.py` should be the main entry point for the evaluation process as per ROADMAP.md.
- Ensure that the agentic flow entry point is cleanly importable so the evaluation harness can query it programmatically and retrieve both the generated answer and the underlying context chunks used.
- Need an Ollama wrapper implementation compatible with RAGAS (either via Langchain `ChatOllama` wrapper or similar) to allow RAGAS to score answers locally offline.
</code_context>

<specifics>
## Specific Ideas

- The naive baseline and agentic graph outputs must be tracked and mapped to Ragas concepts (Question, Answer, Contexts, Ground Truth) accurately.
- Avoid using external APIs by configuring local Ollama backend for RAGAS.
</specifics>

<deferred>
## Deferred Ideas

(None)
</deferred>

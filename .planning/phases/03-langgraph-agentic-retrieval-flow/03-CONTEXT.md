# Phase 3: LangGraph Agentic Retrieval Flow - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the full agentic RAG graph with query routing, retrieval, grading, generation, hallucination checking, and re-retrieval loop using LangGraph.
</domain>

<decisions>
## Implementation Decisions

### Model Selection Correction
- **D-01:** **Overriding prior constraints:** Use `gemma4:e4b` via Ollama for ALL LLM tasks in this phase (Primary generation, Routing, Grading, Hallucination checking) rather than splitting duties with gemma3:4b. 

### Re-retrieval Logic
- **D-02:** Max re-retrieval limit is set to **3 retries**. If the agent cannot find a satisfactory answer within 3 retrieval attempts, it should stop looping.

### Citation Strategy
- **D-03:** Combine both styles. Output should use inline citations (e.g., `[1]`) and include a numbered footnote map at the bottom of the response that ties the inline numbers to the retrieved chunk `source` paths.

### Out-of-Scope Routing
- **D-04:** **Strict filtering.** The router must reject any queries that are not strictly about "Microsoft Azure AI Foundry Agents" and their solutions. General IT, Azure, or unrelated questions immediately trigger the out-of-scope fallback message.

### Relevance Grading
- **D-05:** Binary Yes/No grading. The `grade_documents` LLM judge will determine if a chunk is relevant using a simple Yes/No boolean logic rather than trying to calculate numerical scores or thresholds.
</decisions>

<canonical_refs>
## Canonical References

### Project Requirements
- `.planning/REQUIREMENTS.md`

### Source Assets
- `src/vectorstore.py`
- `src/config.py`
</canonical_refs>

<code_context>
## Existing Code Insights
- `src/vectorstore.py` provides the integration point for document retrieval.
- `src/config.py` contains settings that will need to be updated (e.g., setting `LLM_MODEL` to `gemma4:e4b` so it matches the vision model).
</code_context>

<specifics>
## Specific Ideas
- The routing node needs a strict system prompt clarifying the narrow acceptable topic range.
- The generation node needs strict instructions to enforce both inline and footnote citation styling.
</specifics>

<deferred>
## Deferred Ideas
(None)
</deferred>

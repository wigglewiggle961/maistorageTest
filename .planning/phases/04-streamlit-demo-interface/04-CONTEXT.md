# Phase 4: Streamlit Demo Interface - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Streamlit Chat UI for the Agentic RAG
</domain>

<decisions>
## Implementation Decisions

### Layout Style
- **D-01:** Single center column with expanding sections (Streamlit standard).

### Citation UX
- **D-02:** Both inline citations (e.g. [1]) and an expanded list of sources at the bottom. The inline citations should ideally relate to the sources listed at the bottom.

### Agent Step Transparency
- **D-03:** Both plain-English status messages and raw technical LangGraph node names. Plain-English is primary for users, accompanied by toggleable/expandable raw node traces for developers.

### Chat History UI
- **D-04:** Keep a running scroll of the entire session. The agent remains structurally single-turn per Phase 3, but the UI visibly retains past questions and answers.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
None specifically for UI yet.

### Established Patterns
LangGraph graph execution patterns will need to stream state for transparency.

### Integration Points
Interfacing directly with the LangGraph state/messages from Phase 3.
</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches
</specifics>

<deferred>
## Deferred Ideas

None — analysis stayed within phase scope
</deferred>

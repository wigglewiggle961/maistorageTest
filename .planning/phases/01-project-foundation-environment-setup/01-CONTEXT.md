# Phase 1: Project Foundation & Environment Setup - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the Python project scaffold, install all dependencies, and verify that the three required Ollama models are running and responsive on the developer's local machine. This phase is **local dev only** — no containerization, no Docker, no deployment infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Dependency Management
- **D-01:** Use `requirements.txt` with all Python dependencies pinned (not `pyproject.toml`). Standard pip install workflow.

### Project Layout
- **D-02:** Flat `src/` layout — source modules live directly in `src/` (no nested package structure with `__init__.py` hierarchy). Scripts live in `scripts/`.
- **D-03:** Directory structure: `src/`, `scripts/`, `tests/`, `data/`, `docs/`, `documents/` (existing corpus folder stays as-is).

### Ollama Runtime
- **D-04:** Ollama runs on the **host machine** (not in Docker). The app connects to Ollama's local API at `http://localhost:11434`. No container networking or GPU passthrough configuration required.
- **D-05:** The verify script (`scripts/verify_models.py`) pings the host Ollama API directly — not via a containerized endpoint.

### Docker — DEFERRED
- **D-06:** Docker and `docker-compose.yml` are explicitly **out of scope** for this phase and v1 delivery. The developer wants to focus on local dev only. INFRA-03 and Phase 1 Plan 3 (Docker Compose scaffold) are deferred to a future phase or v2. The planner should **skip** the Docker Compose plan entirely.

### Agent's Discretion
- Exact dependency versions for `requirements.txt` — agent selects stable, compatible versions of LangGraph, langchain, chromadb, streamlit, ragas, ollama-python that are known to work together as of April 2026.
- README structure and formatting — agent decides the layout, covering: install Ollama, pull models, install Python deps, run ingestion, run app.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — INFRA-01 (requirements.txt), INFRA-02 (README), INFRA-03 (Docker — SKIP this one per D-06)

### Assessment Context
- `AssessmentQuestion.md` — The assessment question this project answers; useful for understanding what the README must communicate to evaluators

No external API specs required for this phase — everything connects to local Ollama at `http://localhost:11434`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — fresh project, no existing source code.

### Established Patterns
- None yet — this phase establishes the baseline patterns all subsequent phases build on.

### Integration Points
- `documents/` folder already exists in the project root with the corpus (35+ markdown files, `faq.yml`, `media/`). The project layout must not move or restructure this folder.
- All future phases will import from `src/` and run scripts from `scripts/` — the layout defined here sets the import conventions.

</code_context>

<specifics>
## Specific Ideas

- Ollama base URL should be configurable via environment variable (e.g., `OLLAMA_BASE_URL`, defaulting to `http://localhost:11434`) so it can be overridden without code changes if ever needed.
- The verify script should print a clear pass/fail status for each model, not just a raw API response — it's used as a setup sanity check by new developers following the README.

</specifics>

<deferred>
## Deferred Ideas

- **Docker Compose scaffold (INFRA-03 / Phase 1 Plan 3):** User explicitly dropped Docker for v1. No `docker-compose.yml` needed. If containerization is revisited, it belongs in a future phase or v2 milestone.

</deferred>

---

*Phase: 01-project-foundation-environment-setup*
*Context gathered: 2026-04-16*

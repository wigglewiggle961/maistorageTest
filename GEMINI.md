<!-- GSD:project-start source:PROJECT.md -->
## Project

**Agentic RAG — Microsoft Azure AI Foundry Agent Service Docs**

A locally-running Agentic RAG system built on LangGraph that answers questions about the Microsoft Azure AI Foundry Agent Service using its official markdown documentation as the knowledge base. The system features an agentic retrieval loop (query routing, self-correction, multi-step reasoning) and a Streamlit demo interface. It is built as an assessment deliverable demonstrating prototype, documentation, QA methodology, and optimized retrieval with RAGAS evaluation.

**Core Value:** A RAG agent that accurately retrieves grounded answers from the Azure AI Foundry docs with demonstrably better accuracy than naive retrieval — proven via RAGAS metrics and FAQ-based test cases.

### Constraints

- **Hardware:** RTX 3060 Laptop 6 GB VRAM — all models must fit (gemma3:4b ~3.3 GB, nomic-embed-text ~274 MB, llava for ingest only)
- **Tech Stack:** Python, LangGraph, ChromaDB, Ollama, Streamlit — no cloud dependencies at runtime
- **Scope:** Single-milestone assessment deliverable — working prototype + demo + docs + QA explanation
- **Corpus:** Static `documents/` folder; no live web scraping or API fetching of Azure docs
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.agent/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
